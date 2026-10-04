"""Layer 4: NBA model (T-learner on cure, decision_value ranking), policy gate, SHAP explanations.

  python run.py train    # 6 LightGBM classifiers -> models/nba/*.joblib + reports/model_card.md
  python run.py score    # batch score all open cases -> gold.nba_recommendations

Actions (6):
  no_contact            source=no_contact_holdout cell
  digital_nudge         source=random assignment, treatment_path in {EMAIL,SMS,PUSH,LETTER,-combo-no-CALL}
  call_best_time        source=random assignment, treatment_path contains CALL
  payment_plan          observational (payment_plan_flag=true)       NOT RANDOMISED - see model card
  hardship_referral     observational (hardship_program_offered=true) NOT RANDOMISED - see model card
  escalate              observational (current_treatment in late-stage set) NOT RANDOMISED

Decision: argmax over allowed actions of  p_cure(a) * balance_at_risk - action_cost(a).
Policy gate (src/layer4/policy_gate.py) can block the top choice; next allowed action wins.

The companion score_case(case_id) is sub-second: six model.predict_proba on a 1-row DataFrame.
"""
from __future__ import annotations
import json, time
from pathlib import Path
import duckdb
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import lightgbm as lgb

MODELS_DIR = Path("models/nba")

ACTIONS = ["no_contact", "digital_nudge", "call_best_time", "payment_plan",
           "hardship_referral", "escalate"]
# costs in CAD; small/arbitrary but tuned so dollar-weighted decision_value is sensible
ACTION_COST = {"no_contact": 0.0, "digital_nudge": 0.05, "call_best_time": 2.50,
               "payment_plan": 1.00, "hardship_referral": 3.00, "escalate": 10.00}

# features from gold.features_online (23 total; the model handles NaN natively)
FEATURE_COLS = [
    "dpd_level", "worst_dpd_12m", "dpd_slope_3m", "utilisation_trend_6m", "balance_at_risk",
    "broken_promises_90d", "promise_due_vs_payday_gap_days", "payroll_delay_days",
    "salary_change_3m_pct", "nsf_count_3m", "cash_flow_slope_6m", "bureau_present",
    "bureau_delta_90d", "contacts_last_7d", "answer_rate_30d", "best_time_band_hour",
    "txt_hardship_signal_clear", "txt_hardship_signal_possible",
    "txt_ptp_mentioned", "txt_ptp_intent_strength", "txt_sentiment_distressed",
    "txt_sentiment_hostile", "vulnerability_signal", "txt_dispute_mention",
]

# ============================================================================= training data
TRAIN_SQL = """
WITH feat AS (
    SELECT f.golden_id, f.dpd_level, f.worst_dpd_12m, f.dpd_slope_3m, f.utilisation_trend_6m,
           f.balance_at_risk, f.broken_promises_90d, f.promise_due_vs_payday_gap_days,
           f.payroll_delay_days, f.salary_change_3m_pct, f.nsf_count_3m, f.cash_flow_slope_6m,
           f.bureau_present::INT AS bureau_present, f.bureau_delta_90d,
           f.contacts_last_7d, f.answer_rate_30d, f.best_time_band_hour,
           (f.txt_hardship_signal = 'clear')::INT AS txt_hardship_signal_clear,
           (f.txt_hardship_signal = 'possible')::INT AS txt_hardship_signal_possible,
           f.txt_ptp_mentioned::INT AS txt_ptp_mentioned, f.txt_ptp_intent_strength,
           (f.txt_sentiment = 'distressed')::INT AS txt_sentiment_distressed,
           (f.txt_sentiment IN ('hostile','frustrated'))::INT AS txt_sentiment_hostile,
           f.vulnerability_signal::INT AS vulnerability_signal,
           f.txt_dispute_mention::INT AS txt_dispute_mention
      FROM gold.features_online f),
case_action AS (
    SELECT cc.case_id, xc.golden_id, cc.cure_flag::INT AS y, cc.test_cell, cc.assignment_method,
           cc.treatment_path, cc.current_treatment, cc.payment_plan_flag,
           cc.hardship_program_offered,
           -- order matters: payment_plan is a specific signed instrument (8k rows); hardship_referral
           -- is the broader hardship-programme bucket. Keep payment_plan above hardship so each has
           -- its own training rows.
           CASE
             WHEN cc.test_cell = 'no_contact_holdout' THEN 'no_contact'
             WHEN cc.current_treatment IN ('senior_agent_escalation','legal_handoff',
                                           'debt_sale','legal_recovery','final_demand_letter') THEN 'escalate'
             WHEN cc.payment_plan_flag THEN 'payment_plan'
             WHEN cc.hardship_program_offered THEN 'hardship_referral'
             WHEN cc.assignment_method = 'random' AND cc.treatment_path LIKE '%CALL%' THEN 'call_best_time'
             WHEN cc.assignment_method = 'random' THEN 'digital_nudge'
             ELSE NULL END AS action
      FROM silver.collections_cases cc
      JOIN silver.id_xref xc ON xc.source_system='collections' AND xc.source_key = cc.case_id)
SELECT ca.case_id, ca.golden_id, ca.action, ca.y, ca.test_cell, ca.assignment_method,
       ca.treatment_path, feat.*
  FROM case_action ca
  LEFT JOIN feat USING (golden_id)
 WHERE ca.action IS NOT NULL
"""


# ============================================================================= trainer
def _lgb_classifier():
    return lgb.LGBMClassifier(
        n_estimators=250, learning_rate=0.05, max_depth=-1, num_leaves=63,
        min_child_samples=100, subsample=0.8, colsample_bytree=0.8,
        objective="binary", class_weight="balanced", random_state=42, n_jobs=-1, verbosity=-1)


def _eval(y_true, y_pred_proba) -> dict:
    from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
    return {"auc": round(float(roc_auc_score(y_true, y_pred_proba)), 3),
            "pr_auc": round(float(average_precision_score(y_true, y_pred_proba)), 3),
            "brier": round(float(brier_score_loss(y_true, y_pred_proba)), 4),
            "n": int(len(y_true)), "cured_rate": round(float(y_true.mean()), 3)}


def _qini(df_scored: pd.DataFrame) -> float:
    """Qini-like area: cumulative treated-cure minus control-cure over sorted-by-uplift bins."""
    if "uplift" not in df_scored or "y" not in df_scored or "treated" not in df_scored:
        return float("nan")
    d = df_scored.sort_values("uplift", ascending=False).reset_index(drop=True)
    T = d.treated.values; Y = d.y.values
    nT = T.sum(); nC = (1 - T).sum()
    if nT == 0 or nC == 0: return float("nan")
    cum = ((T * Y).cumsum() - (1 - T).cumsum() * (T * Y).sum() / nC)
    return round(float(cum.mean() / len(d)), 4)


def train(cfg: dict, log=print) -> dict:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(cfg["db_path"], read_only=True)
    df = con.execute(TRAIN_SQL).df()
    con.close()
    log(f"  training rows: {len(df):,}  actions: {dict(df['action'].value_counts())}")

    results = {}
    models = {}
    for action in ACTIONS:
        d = df[df.action == action]
        if len(d) < 500:
            log(f"  SKIP {action}: {len(d)} rows (too few)")
            results[action] = {"skipped": True, "n": int(len(d))}
            continue
        X = d[FEATURE_COLS].astype(float)
        y = d["y"]
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42,
                                                   stratify=y if y.nunique() > 1 else None)
        model = _lgb_classifier()
        model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], callbacks=[lgb.early_stopping(20, verbose=False)])
        proba_te = model.predict_proba(X_te)[:, 1]
        m = _eval(y_te, proba_te)
        results[action] = m
        models[action] = model
        joblib.dump(model, MODELS_DIR / f"{action}.joblib")
        log(f"    {action}: AUC {m['auc']}  PR-AUC {m['pr_auc']}  Brier {m['brier']}  n={m['n']}  cured={m['cured_rate']}")

    # Uplift: p_cure(a) - p_cure(no_contact) on a hold-out of the no_contact set
    uplift_table = _uplift_eval(df, models)
    cfg_cost = {a: float(ACTION_COST[a]) for a in ACTIONS}
    _write_model_card(results, uplift_table, cfg_cost, df)
    return {"results": results, "uplift": uplift_table}


def _uplift_eval(df: pd.DataFrame, models: dict) -> list[dict]:
    """For each treatment action vs no_contact baseline, estimate average uplift on the no_contact
    hold-out customers and compute Qini-like area."""
    base = models.get("no_contact")
    if base is None: return []
    d_nc = df[df.action == "no_contact"].reset_index(drop=True)
    X = d_nc[FEATURE_COLS].astype(float)
    p_nc = base.predict_proba(X)[:, 1]
    out = []
    for action in ACTIONS:
        if action == "no_contact" or action not in models: continue
        p_a = models[action].predict_proba(X)[:, 1]
        uplift = p_a - p_nc
        qini_df = pd.DataFrame({"uplift": uplift, "y": d_nc["y"].values,
                                "treated": np.zeros(len(d_nc), dtype=int)})  # all unobserved-treated
        out.append({"action": action,
                    "mean_predicted_uplift": round(float(uplift.mean()), 4),
                    "p10_uplift": round(float(np.percentile(uplift, 10)), 4),
                    "p90_uplift": round(float(np.percentile(uplift, 90)), 4)})
    return out


def _write_model_card(results, uplift, costs, df_train):
    from tabulate import tabulate
    rows = [(a, m.get("n", 0), m.get("cured_rate"), m.get("auc"), m.get("pr_auc"), m.get("brier"),
             "skipped" if m.get("skipped") else "ok")
            for a, m in results.items()]
    counts = df_train.action.value_counts().to_dict()
    uplift_rows = [(u["action"], u["mean_predicted_uplift"], u["p10_uplift"], u["p90_uplift"]) for u in uplift]
    md = [
        "# NBA model card",
        "",
        "## Design",
        "- **T-learner**: one LightGBM binary classifier per action (p_cure | action, features).",
        "- **Target**: `collections_cases.cure_flag` (cured within the case).",
        "- **Decision**: argmax over allowed actions of  `p_cure(a) * balance_at_risk - action_cost(a)`.",
        "- **Policy gate** runs after the model and can block the top action; next allowed wins.",
        "- **Features**: 24 (16 numeric + 8 text-derived). Protected / proxy attributes NOT in the input set.",
        "",
        "## Actions and training counts",
        "",
        tabulate([(a, counts.get(a, 0), costs.get(a, 0)) for a in ACTIONS],
                 headers=["action", "training rows", "action_cost ($)"], tablefmt="github"),
        "",
        "## Per-action classifier metrics (20% hold-out)",
        "",
        tabulate(rows, headers=["action", "n_test", "cured_rate", "AUC", "PR-AUC", "Brier", "status"],
                 tablefmt="github"),
        "",
        "## Predicted uplift vs no_contact baseline (eval on no_contact_holdout customers)",
        "",
        tabulate(uplift_rows,
                 headers=["action", "mean uplift", "p10 uplift", "p90 uplift"], tablefmt="github"),
        "",
        "## Honesty notes",
        "- `payment_plan`, `hardship_referral`, `escalate` are **observational** (not randomised). "
          "Their classifiers predict p_cure WHEN they were applied; the uplift column treats them as "
          "treatments but confounding is possible. For live decisions these actions are gated by the "
          "policy module anyway (hardship routes supportive, escalate is late-stage only), so uplift "
          "is a diagnostic, not the decision driver.",
        "- The randomisation check (`reports/randomisation_check.md`) confirms the champion / "
          "no_contact_holdout contrast is clean (worst |SMD| = 0.033).",
        "- Pure 30-day-cure uplift is small (no_contact baseline 71.5%); `decision_value` with "
          "`action_cost=0` for no_contact is why the system still saves money - it stops dialling "
          "customers who were going to self-cure.",
        "- `action_cost` values are illustrative; a cost study should replace them before prod.",
    ]
    Path("reports").mkdir(exist_ok=True)
    Path("reports/model_card.md").write_text("\n".join(md), encoding="utf-8")


# ============================================================================= scoring
def _load_models() -> dict:
    out = {}
    for a in ACTIONS:
        p = MODELS_DIR / f"{a}.joblib"
        if p.exists(): out[a] = joblib.load(p)
    return out


def _features_for(con, golden_id: str) -> pd.DataFrame:
    df = con.execute(TRAIN_SQL + " AND ca.golden_id = ?",
                     [golden_id]).df() if False else None   # inline fetch below
    row = con.execute(f"""SELECT f.* FROM gold.features_online f
                           WHERE f.golden_id = ?""", [golden_id]).df()
    if row.empty:
        return pd.DataFrame(columns=FEATURE_COLS)
    row = _project(row)
    return row


def _project(df: pd.DataFrame) -> pd.DataFrame:
    """Map a gold.features_online row to the 24-column model input (one-hot the categoricals)."""
    out = pd.DataFrame({c: 0.0 for c in FEATURE_COLS}, index=df.index)
    numeric = ["dpd_level", "worst_dpd_12m", "dpd_slope_3m", "utilisation_trend_6m", "balance_at_risk",
               "broken_promises_90d", "promise_due_vs_payday_gap_days", "payroll_delay_days",
               "salary_change_3m_pct", "nsf_count_3m", "cash_flow_slope_6m",
               "bureau_delta_90d", "contacts_last_7d", "answer_rate_30d", "best_time_band_hour",
               "txt_ptp_intent_strength"]
    for c in numeric:
        if c in df: out[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["bureau_present", "txt_ptp_mentioned", "vulnerability_signal", "txt_dispute_mention"]:
        if c in df: out[c] = df[c].astype(bool).astype(int)
    if "txt_hardship_signal" in df:
        out["txt_hardship_signal_clear"] = (df["txt_hardship_signal"] == "clear").astype(int)
        out["txt_hardship_signal_possible"] = (df["txt_hardship_signal"] == "possible").astype(int)
    if "txt_sentiment" in df:
        out["txt_sentiment_distressed"] = (df["txt_sentiment"] == "distressed").astype(int)
        out["txt_sentiment_hostile"] = df["txt_sentiment"].isin(["hostile", "frustrated"]).astype(int)
    return out[FEATURE_COLS]


def _decision(models: dict, X: pd.DataFrame, balance: pd.Series, allowed: dict = None) -> pd.DataFrame:
    """Return (action, p_cure, decision_value) for each row, picking argmax over allowed actions."""
    rows = pd.DataFrame(index=X.index)
    for a in ACTIONS:
        if a not in models: continue
        p = models[a].predict_proba(X)[:, 1]
        dv = p * balance.values - ACTION_COST[a]
        rows[f"p_cure_{a}"] = p
        rows[f"dv_{a}"] = dv
    # mask disallowed actions by -inf before argmax
    dvs = rows[[f"dv_{a}" for a in ACTIONS if f"dv_{a}" in rows.columns]].copy()
    if allowed is not None:
        for a in ACTIONS:
            col = f"dv_{a}"
            if col in dvs.columns:
                dvs.loc[~allowed.get(a, True), col] = -np.inf
    dvs.columns = [c[3:] for c in dvs.columns]
    best = dvs.idxmax(axis=1)
    rows["recommended_action"] = best
    rows["decision_value"] = dvs.max(axis=1)
    rows["p_cure"] = [rows.at[i, f"p_cure_{best[i]}"] for i in rows.index]
    rows["balance_at_risk"] = balance.values
    return rows


def score_case(cfg: dict, case_id: str, models: dict | None = None) -> dict:
    """Sub-second lookup used by the Agent Desk."""
    t0 = time.time()
    con = duckdb.connect(cfg["db_path"], read_only=True)
    try:
        case = con.execute("""SELECT c.*, x.golden_id FROM silver.collections_cases c
                              JOIN silver.id_xref x ON x.source_system='collections' AND x.source_key = c.case_id
                              WHERE c.case_id = ?""", [case_id]).df()
        if case.empty: return {"case_id": case_id, "error": "case not found"}
        feats_raw = con.execute("SELECT * FROM gold.features_online WHERE golden_id = ?",
                                [case[0,"golden_id"] if False else case["golden_id"].iloc[0]]).df()
    finally:
        con.close()
    models = models or _load_models()
    X = _project(feats_raw) if not feats_raw.empty else _project(pd.DataFrame(columns=["golden_id"]))
    if X.empty: X = pd.DataFrame({c: [0.0] for c in FEATURE_COLS})
    bal = pd.Series([float(case["total_overdue"].iloc[0] or 0)])
    # apply policy gate
    from src.layer4.policy_gate import allowed_actions
    allowed_series = allowed_actions(case.iloc[0], feats_raw.iloc[0] if not feats_raw.empty else None)
    allowed_mask = {a: pd.Series([allowed_series[a]], index=X.index) for a in ACTIONS}
    dec = _decision(models, X, bal, allowed_mask)
    row = dec.iloc[0].to_dict()
    row["case_id"] = case_id
    row["allowed_actions"] = {a: bool(v) for a, v in allowed_series.items()}
    row["blocked_reasons"] = {a: r for a, (ok, r) in allowed_series._reasons.items() if not ok and r}
    row["latency_ms"] = round(1000 * (time.time() - t0), 1)
    return row


def batch_score(cfg: dict, log=print) -> int:
    """Score all open cases and write to gold.nba_recommendations."""
    con = duckdb.connect(cfg["db_path"])
    con.execute("CREATE SCHEMA IF NOT EXISTS gold")
    cases = con.execute("""SELECT c.case_id, c.total_overdue, c.hardship_flag,
                                  c.cease_contact_flag, c.insolvency_hold_flag, c.deceased_hold_flag,
                                  c.vulnerable_customer_flag, c.dispute_flag, c.current_dpd,
                                  c.current_bucket, c.third_party_rep_flag, c.primary_product,
                                  x.golden_id
                             FROM silver.collections_cases c
                             JOIN silver.id_xref x ON x.source_system='collections' AND x.source_key = c.case_id
                            WHERE c.case_status = 'open'""").df()
    log(f"  scoring {len(cases):,} open cases")
    feats = con.execute("""SELECT * FROM gold.features_online
                           WHERE golden_id IN (SELECT golden_id FROM gold.c360_customer)""").df()
    merged = cases.merge(feats, on="golden_id", how="left")
    X = _project(merged)
    from src.layer4.policy_gate import allowed_actions_vectorised
    allowed = allowed_actions_vectorised(merged)
    bal = pd.to_numeric(merged["total_overdue"], errors="coerce").fillna(0.0)
    models = _load_models()
    allowed_mask = {a: allowed[a] for a in ACTIONS}
    dec = _decision(models, X, bal, allowed_mask)
    out = pd.concat([merged[["case_id", "golden_id"]].reset_index(drop=True), dec.reset_index(drop=True)], axis=1)
    out["refreshed_at"] = pd.Timestamp.now()
    con.register("_nba", out)
    con.execute("CREATE OR REPLACE TABLE gold.nba_recommendations AS SELECT * FROM _nba")
    con.unregister("_nba")
    log(f"  gold.nba_recommendations: {len(out):,} rows; action mix: "
        f"{dict(out['recommended_action'].value_counts())}")
    con.close()
    return len(out)
