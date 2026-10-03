"""Text features: TF-IDF (word + char) + logistic regression on the 500 public note / transcript
labels. Scores all 760k notes and 25k transcripts on CPU. No LLM, no GPU.

Fields trained (public_500 label subset):
  hardship (3-class: none / possible / clear)
  delay_reason (collapsed to top-5 + "other")
  ptp_mentioned (bool)
  ptp_intent_strength (regression 0..1, when ptp_mentioned=true)
  sentiment (4-class)
  vulnerability (bool; see caveat below)
  next_step (DIAGNOSTIC ONLY - not a model input)

Rules (sparse labels, use regex):
  dispute_mention, legal_threat_by_agent (QA)

Vulnerability caveat: 55 positives in notes / 82 in transcripts. We expose it via
`vulnerability_signal = structured_vulnerability_flag OR (classifier_true AND confidence > 0.8)`
in features.py; the classifier here only tips the signal TRUE, never FALSE.

Output tables:
  gold.text_features_notes       (note_id, hardship, delay_reason, ptp_mentioned,
                                  ptp_intent_strength, sentiment, vulnerability_pred,
                                  vulnerability_conf, next_step, dispute_mention, lang)
  gold.text_features_transcripts (transcript_id, same columns, plus legal_threat_by_agent)
"""
from __future__ import annotations
import json, re, time
from pathlib import Path
import duckdb
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.metrics import classification_report, precision_recall_fscore_support, mean_absolute_error
from sklearn.pipeline import FeatureUnion, Pipeline

MODELS_DIR = Path("models/text")
TRANSCRIPTS_ROOT = Path("../maple_data/maple_collections_release/files")


# ------------------------------------------------------------------------------ regex rules
_RE_DISPUTE = re.compile(
    r"\b(dispute|not\s+authori[sz]ed|unauthori[sz]ed|charge\s*back|chargeback|wrong\s+charge|"
    r"double\s+charge|refund|billing\s+error|conteste|contester|frais|rembours)\b",
    re.I)
_RE_LEGAL = re.compile(
    r"\b(sue|lawsuit|court|garnish|garnishment|lien|jail|arrest|legal\s+action|take\s+your|"
    r"we\s+will\s+take|avocat|poursuite|tribunal|saisie)\b", re.I)


def regex_dispute(text: str) -> bool:
    if not text: return False
    return bool(_RE_DISPUTE.search(text)) and "no dispute" not in text.lower()


def regex_legal_threat(text: str) -> bool:
    if not text: return False
    return bool(_RE_LEGAL.search(text))


# ------------------------------------------------------------------------------ model utilities
def _vectorizer():
    """Word + char n-grams in a single feature union; char n-grams carry French OK on small data."""
    return FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, lowercase=True,
                                 sublinear_tf=True, strip_accents="unicode")),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, max_df=0.95,
                                 lowercase=True, sublinear_tf=True)),
    ])


def _train_classifier(X, y, name: str) -> tuple[Pipeline, dict]:
    """5-fold CV with class-balanced logistic regression, then fit on all. Returns (model, metrics)."""
    pipe = Pipeline([("vec", _vectorizer()),
                     ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", n_jobs=-1))])
    classes, counts = np.unique(y, return_counts=True)
    strat_ok = counts.min() >= 5
    if strat_ok and len(y) >= 25:
        splits = min(5, int(counts.min()))
        cv = StratifiedKFold(n_splits=splits, shuffle=True, random_state=42)
        y_cv = cross_val_predict(pipe, X, y, cv=cv, n_jobs=1)
        p, r, f1, s = precision_recall_fscore_support(y, y_cv, average=None, zero_division=0, labels=classes)
        macro = precision_recall_fscore_support(y, y_cv, average="macro", zero_division=0)
        metrics = {"name": name, "classes": classes.tolist(),
                   "per_class": [{"class": str(c), "precision": round(p[i], 3), "recall": round(r[i], 3),
                                  "f1": round(f1[i], 3), "support": int(s[i])} for i, c in enumerate(classes)],
                   "macro_f1": round(macro[2], 3), "n": int(len(y))}
    else:
        metrics = {"name": name, "classes": classes.tolist(), "per_class": [],
                   "macro_f1": None, "n": int(len(y)), "note": "too few positives for CV"}
    pipe.fit(X, y)
    return pipe, metrics


def _train_regressor(X, y, name: str) -> tuple[Pipeline, dict]:
    pipe = Pipeline([("vec", _vectorizer()), ("reg", Ridge(alpha=1.0))])
    if len(y) < 25:
        pipe.fit(X, y)
        return pipe, {"name": name, "mae_cv": None, "n": int(len(y)), "note": "too few samples for CV"}
    y_cv = cross_val_predict(pipe, X, y, cv=min(5, len(y) // 10), n_jobs=1)
    mae = mean_absolute_error(y, y_cv)
    pipe.fit(X, y)
    return pipe, {"name": name, "mae_cv": round(mae, 3), "n": int(len(y))}


# ------------------------------------------------------------------------------ label collapse
_TOP_DELAY = {"reduced_income", "forgot", "dispute", "timing", "other"}


def _collapse_delay(s):
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return "unknown"
    s = str(s).strip()
    if not s:
        return "unknown"
    return s if s in _TOP_DELAY else "other"


# ------------------------------------------------------------------------------ transcript body loader
def _load_transcript_text(file_path: str) -> str:
    try:
        j = json.loads((TRANSCRIPTS_ROOT / file_path).read_text(encoding="utf-8"))
        return " ".join(t.get("text", "") for t in j.get("turns", []) if t.get("text"))
    except Exception:
        return ""


# ------------------------------------------------------------------------------ train + score
def train_and_score(cfg: dict, log=print) -> dict:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(cfg["db_path"])
    con.execute("CREATE SCHEMA IF NOT EXISTS gold")
    scfg = cfg.get("silver", {})
    con.execute(f"SET memory_limit='{scfg.get('memory_limit', '4GB')}'; "
                f"SET threads={int(scfg.get('threads', 4))}")

    # ----------------- NOTES: training set -----------------
    log("  loading labelled notes...")
    nb = con.execute("""
        SELECT n.note_id, coalesce(n.note_text, '') AS text,
               lbl.label_hardship, lbl.label_stated_delay_reason, lbl.label_ptp_mentioned,
               lbl.label_ptp_intent_strength, lbl.label_sentiment, lbl.label_vulnerability,
               lbl.label_next_step
          FROM hidden.agent_notes_labels_public_500 lbl
          JOIN silver.agent_notes n ON n.note_id = lbl.note_id""").df()
    log(f"  notes labelled rows: {len(nb)}")

    metrics = {"notes": {}, "transcripts": {}}
    models = {}
    # train note classifiers
    for col, name, kind in [
        ("label_hardship", "hardship", "cls"),
        ("label_stated_delay_reason", "delay_reason", "cls_delay"),
        ("label_ptp_mentioned", "ptp_mentioned", "cls"),
        ("label_sentiment", "sentiment", "cls"),
        ("label_vulnerability", "vulnerability", "cls"),
        ("label_next_step", "next_step", "cls"),
        ("label_ptp_intent_strength", "ptp_intent_strength", "reg"),
    ]:
        X, y = nb["text"].tolist(), nb[col]
        if kind == "cls_delay":
            y = y.map(_collapse_delay)
            kind = "cls"
        mask = y.notna() & (y.astype(str) != "")
        if mask.sum() < 20:
            log(f"  SKIP {name}: only {mask.sum()} labelled rows")
            metrics["notes"][name] = {"skipped": True, "n": int(mask.sum())}
            continue
        if kind == "reg":
            y_num = pd.to_numeric(y[mask], errors="coerce")
            mask2 = y_num.notna()
            model, m = _train_regressor([X[i] for i, ok in enumerate(mask) if ok and mask2.iloc[sum(mask.iloc[:i+1]) - 1]],
                                        y_num[mask2].values, name)
        else:
            model, m = _train_classifier([X[i] for i, ok in enumerate(mask) if ok], y[mask].astype(str).tolist(), name)
        models[f"notes_{name}"] = model
        metrics["notes"][name] = m
        joblib.dump(model, MODELS_DIR / f"notes_{name}.joblib")
        log(f"    notes/{name}: {m.get('macro_f1') if 'macro_f1' in m else m.get('mae_cv')} (n={m.get('n')})")

    # ----------------- TRANSCRIPTS: load bodies for the 500 labelled, train -----------------
    log("  loading labelled transcripts (reading 500 JSON files)...")
    tb_meta = con.execute("""
        SELECT CAST(ct.transcript_id AS VARCHAR) AS transcript_id, ct.file_path, ct.language,
               lbl.label_hardship, lbl.label_stated_delay_reason, lbl.label_ptp_mentioned,
               lbl.label_ptp_intent_strength, lbl.label_sentiment, lbl.label_vulnerability,
               lbl.label_next_step
          FROM hidden.call_transcripts_labels_public_500 lbl
          JOIN main.call_transcripts ct ON CAST(ct.transcript_id AS VARCHAR) = CAST(lbl.transcript_id AS VARCHAR)
    """).df()
    tb_meta["text"] = tb_meta["file_path"].map(_load_transcript_text)
    tb_meta = tb_meta[tb_meta["text"].str.len() > 0]
    log(f"  transcripts labelled rows: {len(tb_meta)}")

    for col, name, kind in [
        ("label_hardship", "hardship", "cls"),
        ("label_stated_delay_reason", "delay_reason", "cls_delay"),
        ("label_ptp_mentioned", "ptp_mentioned", "cls"),
        ("label_sentiment", "sentiment", "cls"),
        ("label_vulnerability", "vulnerability", "cls"),
        ("label_next_step", "next_step", "cls"),
        ("label_ptp_intent_strength", "ptp_intent_strength", "reg"),
    ]:
        y = tb_meta[col]
        if kind == "cls_delay":
            y = y.map(_collapse_delay); kind = "cls"
        mask = y.notna() & (y.astype(str) != "")
        if mask.sum() < 20:
            metrics["transcripts"][name] = {"skipped": True, "n": int(mask.sum())}; continue
        X = tb_meta.loc[mask, "text"].tolist()
        yv = y[mask]
        if kind == "reg":
            yn = pd.to_numeric(yv, errors="coerce"); mm = yn.notna()
            X = [X[i] for i in range(len(X)) if mm.iloc[i]]; yn = yn[mm].values
            model, m = _train_regressor(X, yn, name)
        else:
            model, m = _train_classifier(X, yv.astype(str).tolist(), name)
        models[f"transcripts_{name}"] = model
        metrics["transcripts"][name] = m
        joblib.dump(model, MODELS_DIR / f"transcripts_{name}.joblib")
        log(f"    transcripts/{name}: {m.get('macro_f1') if 'macro_f1' in m else m.get('mae_cv')} (n={m.get('n')})")

    # ----------------- SCORE ALL notes/transcripts -----------------
    _score_notes(con, models, log)
    _score_transcripts(con, models, log)
    _write_eval_report(metrics)
    con.close()
    return metrics


def _predict_with_conf(model, texts):
    """Return (preds, max-prob confidence) arrays; both len(texts)."""
    preds = model.predict(texts)
    try:
        probs = model.predict_proba(texts)
        conf = probs.max(axis=1)
    except Exception:
        conf = np.ones(len(preds))
    return preds, conf


def _score_notes(con, models, log):
    log("  scoring all notes...")
    t0 = time.time()
    chunk_size = 100_000
    con.execute("""CREATE OR REPLACE TABLE gold.text_features_notes (
        note_id VARCHAR, hardship VARCHAR, delay_reason VARCHAR, ptp_mentioned BOOLEAN,
        ptp_intent_strength DOUBLE, sentiment VARCHAR, vulnerability_pred BOOLEAN,
        vulnerability_conf DOUBLE, next_step VARCHAR, dispute_mention BOOLEAN, lang VARCHAR)""")
    total = con.execute("SELECT count(*) FROM silver.agent_notes").fetchone()[0]
    offset = 0
    while offset < total:
        df = con.execute(f"""SELECT note_id, coalesce(note_text, '') AS text
                             FROM silver.agent_notes ORDER BY note_id LIMIT {chunk_size} OFFSET {offset}""").df()
        if df.empty: break
        texts = df["text"].tolist()
        out = pd.DataFrame({"note_id": df["note_id"]})
        hp, _ = _predict_with_conf(models["notes_hardship"], texts); out["hardship"] = hp
        dp, _ = _predict_with_conf(models["notes_delay_reason"], texts); out["delay_reason"] = dp
        pp, _ = _predict_with_conf(models["notes_ptp_mentioned"], texts); out["ptp_mentioned"] = (pp == "true")
        try:
            ip = models["notes_ptp_intent_strength"].predict(texts); out["ptp_intent_strength"] = np.clip(ip, 0, 1)
        except Exception:
            out["ptp_intent_strength"] = None
        sp, _ = _predict_with_conf(models["notes_sentiment"], texts); out["sentiment"] = sp
        vp, vc = _predict_with_conf(models["notes_vulnerability"], texts)
        out["vulnerability_pred"] = (vp == "true"); out["vulnerability_conf"] = vc
        nx, _ = _predict_with_conf(models["notes_next_step"], texts); out["next_step"] = nx
        out["dispute_mention"] = [regex_dispute(t) for t in texts]
        out["lang"] = ["FR" if re.search(r"[àâéèêëîïôùûç]", t) else "EN" for t in texts]
        con.register("_chunk", out)
        con.execute("INSERT INTO gold.text_features_notes SELECT * FROM _chunk")
        con.unregister("_chunk")
        offset += chunk_size
        log(f"    scored {min(offset, total):,}/{total:,} notes ({time.time()-t0:.0f}s)")
    log(f"  gold.text_features_notes: "
        f"{con.execute('SELECT count(*) FROM gold.text_features_notes').fetchone()[0]:,} rows "
        f"({time.time()-t0:.1f}s)")


def _score_transcripts(con, models, log):
    log("  scoring all transcripts (reading 25k JSON files)...")
    t0 = time.time()
    con.execute("""CREATE OR REPLACE TABLE gold.text_features_transcripts (
        transcript_id VARCHAR, hardship VARCHAR, delay_reason VARCHAR, ptp_mentioned BOOLEAN,
        ptp_intent_strength DOUBLE, sentiment VARCHAR, vulnerability_pred BOOLEAN,
        vulnerability_conf DOUBLE, next_step VARCHAR, dispute_mention BOOLEAN,
        legal_threat_by_agent BOOLEAN, lang VARCHAR)""")
    all_tr = con.execute("""SELECT CAST(transcript_id AS VARCHAR) AS transcript_id, file_path, language
                            FROM main.call_transcripts ORDER BY transcript_id""").df()
    all_tr["text"] = all_tr["file_path"].map(_load_transcript_text)
    all_tr = all_tr[all_tr["text"].str.len() > 0].reset_index(drop=True)
    texts = all_tr["text"].tolist()
    out = pd.DataFrame({"transcript_id": all_tr["transcript_id"]})
    hp, _ = _predict_with_conf(models["transcripts_hardship"], texts); out["hardship"] = hp
    dp, _ = _predict_with_conf(models["transcripts_delay_reason"], texts); out["delay_reason"] = dp
    pp, _ = _predict_with_conf(models["transcripts_ptp_mentioned"], texts); out["ptp_mentioned"] = (pp == "true")
    try:
        ip = models["transcripts_ptp_intent_strength"].predict(texts); out["ptp_intent_strength"] = np.clip(ip, 0, 1)
    except Exception:
        out["ptp_intent_strength"] = None
    sp, _ = _predict_with_conf(models["transcripts_sentiment"], texts); out["sentiment"] = sp
    vp, vc = _predict_with_conf(models["transcripts_vulnerability"], texts)
    out["vulnerability_pred"] = (vp == "true"); out["vulnerability_conf"] = vc
    nx, _ = _predict_with_conf(models["transcripts_next_step"], texts); out["next_step"] = nx
    out["dispute_mention"] = [regex_dispute(t) for t in texts]
    out["legal_threat_by_agent"] = [regex_legal_threat(t) for t in texts]
    out["lang"] = all_tr["language"].tolist()
    con.register("_chunk", out)
    con.execute("INSERT INTO gold.text_features_transcripts SELECT * FROM _chunk")
    con.unregister("_chunk")
    log(f"  gold.text_features_transcripts: "
        f"{con.execute('SELECT count(*) FROM gold.text_features_transcripts').fetchone()[0]:,} rows "
        f"({time.time()-t0:.1f}s)")


def _write_eval_report(metrics: dict, out: str = "reports/text_feature_eval.md") -> str:
    from tabulate import tabulate
    md = ["# Text feature evaluation (5-fold cross-validation on public_500 labels)", "",
          "TF-IDF (word 1-2 grams + char 3-5 grams) + logistic regression (class_weight='balanced').",
          "ptp_intent_strength: Ridge regressor; metric is MAE.",
          "", "## Notes (500 labels)", ""]
    rows = []
    for name, m in metrics["notes"].items():
        if m.get("skipped"):
            rows.append((name, "SKIP", "-", f"too sparse (n={m['n']})"))
            continue
        headline = (f"macro F1 {m['macro_f1']}" if "macro_f1" in m and m["macro_f1"] is not None
                    else f"MAE {m['mae_cv']}" if "mae_cv" in m and m["mae_cv"] is not None
                    else "n/a")
        rows.append((name, m["n"], headline, ", ".join(f"{c['class']}:{c['f1']}" for c in m.get("per_class", []))))
    md.append(tabulate(rows, headers=["field", "n", "overall", "per-class F1"], tablefmt="github"))
    md += ["", "## Transcripts (500 labels)", ""]
    rows = []
    for name, m in metrics["transcripts"].items():
        if m.get("skipped"):
            rows.append((name, "SKIP", "-", f"too sparse (n={m['n']})")); continue
        headline = (f"macro F1 {m['macro_f1']}" if "macro_f1" in m and m["macro_f1"] is not None
                    else f"MAE {m['mae_cv']}" if "mae_cv" in m and m["mae_cv"] is not None
                    else "n/a")
        rows.append((name, m["n"], headline, ", ".join(f"{c['class']}:{c['f1']}" for c in m.get("per_class", []))))
    md.append(tabulate(rows, headers=["field", "n", "overall", "per-class F1"], tablefmt="github"))
    md += ["",
           "## Caveats",
           "- Vulnerability positives: 55 (notes) / 82 (transcripts). F1 is low-variance; treat as a tip, not a verdict. "
           "The feature store exposes `vulnerability_signal = structured_vulnerability_flag OR (classifier_true AND confidence > 0.8)`.",
           "- Delay reason collapsed to top-5 + 'other' to keep per-class support >=20.",
           "- next_step is a diagnostic only (never a model input); feeds a later policy-vs-agent-step governance check.",
           "- Rules (regex): dispute_mention, legal_threat_by_agent. Not scored here."]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(md), encoding="utf-8")
    return out
