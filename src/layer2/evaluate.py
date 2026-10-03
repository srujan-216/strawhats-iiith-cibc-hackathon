"""Score our answers against the dev gold answers (dev split only; test is hidden).
Numeric answers: first number in each answer, compared with the question's tolerance.
Text answers: listed for manual review. Refusals: precision and recall."""
from __future__ import annotations
import re
from pathlib import Path
import duckdb
import pandas as pd

_NUM = re.compile(r"-?\d[\d,]*\.?\d*")


def _num(s):
    m = _NUM.search(str(s))
    return float(m.group(0).replace(",", "")) if m else None


def _tol(t, gold):
    """'0.5' -> abs 0.5; '1%' or '1 pct' -> relative 1% of gold; empty -> 1e-6 relative."""
    t = str(t or "").lower().strip()
    v = _num(t)
    if v is None:
        return abs(gold) * 1e-6 + 1e-9
    if "%" in t and "pp" not in t and "point" not in t:
        return abs(gold) * v / 100
    return v


def _bool(x):
    return str(x).strip().lower() in ("true", "1", "yes", "y")


def evaluate(cfg, ours_csv: str, out_md: str) -> dict:
    con = duckdb.connect(cfg["db_path"], read_only=True)
    gold = con.execute("SELECT * FROM hidden.benchmark_dev_answers").df().astype(str)
    qs = con.execute("SELECT * FROM main.benchmark_questions").df().astype(str)
    con.close()
    ours = pd.read_csv(ours_csv, dtype=str)
    m = gold.merge(ours, on="question_id", suffixes=("_gold", "_ours"), how="left")
    m = m.merge(qs[[c for c in ("question_id", "question_text", "question_type", "tolerance") if c in qs.columns]],
                on="question_id", how="left")
    rows, ok = [], 0
    for _, r in m.iterrows():
        gref, oref = _bool(r.get("refused_gold")), _bool(r.get("refused_ours"))
        g, o = _num(r.get("answer_gold")), _num(r.get("answer_ours"))
        if gref or oref:
            verdict = "ok" if gref == oref else "refusal mismatch"
        elif g is not None and o is not None:
            verdict = "ok" if abs(g - o) <= _tol(r.get("tolerance"), g) else f"off ({o} vs {g})"
        else:
            verdict = "review"
        ok += verdict == "ok"
        rows.append((r["question_id"], r.get("question_type", ""), verdict,
                     str(r.get("answer_ours", ""))[:90], str(r.get("answer_gold", ""))[:90]))
    df = pd.DataFrame(rows, columns=["question_id", "type", "verdict", "ours", "gold"])
    ref_g, ref_o = m["refused_gold"].map(_bool), m["refused_ours"].map(_bool)
    stats = {"n": len(df), "ok": ok, "accuracy": round(ok / max(len(df), 1), 3),
             "refusal_recall": round(float((ref_g & ref_o).sum()) / max(int(ref_g.sum()), 1), 3),
             "refusal_precision": round(float((ref_g & ref_o).sum()) / max(int(ref_o.sum()), 1), 3),
             "needs_review": int((df.verdict == "review").sum())}
    Path(out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(out_md).write_text("# Benchmark dev evaluation\n\n" + "\n".join(f"- {k}: {v}" for k, v in stats.items())
                            + "\n\n" + df.to_markdown(index=False), encoding="utf-8")
    return stats
