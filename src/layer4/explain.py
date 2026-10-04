"""SHAP top-3 features for the recommended action, mapped to plain-English templates +
evidence ids (note_id, transcript_id, policy section). The LLM does not write explanations
(CLAUDE.md section 5)."""
from __future__ import annotations
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
import shap
from src.layer4.nba import FEATURE_COLS, ACTIONS, MODELS_DIR

# Human-friendly phrasing per feature. The direction string flips when the SHAP contribution
# is negative; otherwise we drop the feature from the top-3 (keep only positive contributors).
_TEMPLATES = {
    "worst_dpd_12m": "worst DPD in the last 12 months = {v} days",
    "dpd_level": "current DPD = {v} days",
    "dpd_slope_3m": "DPD rose by {v} days in the last 3 months" if True else "",
    "utilisation_trend_6m": "card utilisation rose by {v:.0%} over 6 months",
    "balance_at_risk": "{v:,.0f} at risk across accounts",
    "broken_promises_90d": "{v} broken promises in the last 90 days",
    "promise_due_vs_payday_gap_days": "promise due {v} days before payroll (negative = after)",
    "payroll_delay_days": "payroll delayed {v} days",
    "salary_change_3m_pct": "salary changed {v:+.0%} over 3 months",
    "nsf_count_3m": "{v} NSF events in the last 3 months",
    "cash_flow_slope_6m": "net cash-flow direction = {v:+.2f} (positive = resilient)",
    "bureau_present": "bureau pull available",
    "bureau_delta_90d": "bureau score changed {v:+d} in 90 days",
    "contacts_last_7d": "{v} contact attempts in the last 7 days",
    "answer_rate_30d": "{v:.0%} right-party-contact rate on recent calls",
    "best_time_band_hour": "best historical answer hour = {v:.0f}:00",
    "txt_hardship_signal_clear": "notes/transcripts indicate clear hardship",
    "txt_hardship_signal_possible": "notes/transcripts indicate possible hardship",
    "txt_ptp_mentioned": "customer mentioned a payment intent",
    "txt_ptp_intent_strength": "stated intent strength = {v:.0%}",
    "txt_sentiment_distressed": "sentiment on recent texts = distressed",
    "txt_sentiment_hostile": "sentiment on recent texts = hostile/frustrated",
    "vulnerability_signal": "customer has a vulnerability signal",
    "txt_dispute_mention": "customer mentioned a dispute in recent texts",
}

_ACTION_WHY = {
    "no_contact": "Recommended because self-cure is likely for this customer; contact adds cost without lift.",
    "digital_nudge": "Recommended because the model predicts a small lift from a payment-link SMS/email, cheap to send.",
    "call_best_time": "Recommended because this customer answers calls and the model predicts a meaningful lift from a voice conversation.",
    "payment_plan": "Recommended because repayment capacity is positive but the current obligation is above affordability.",
    "hardship_referral": "Recommended because the customer shows hardship signals; route to a certified agent and the hardship program catalogue.",
    "escalate": "Recommended because the case has not responded to standard treatment; escalate to senior agent or legal track.",
}


_explainer_cache = {}


def _explainer(action: str):
    if action in _explainer_cache: return _explainer_cache[action]
    model = joblib.load(MODELS_DIR / f"{action}.joblib")
    e = shap.TreeExplainer(model.booster_)
    _explainer_cache[action] = e
    return e


def _format_val(col, v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "n/a"
    tmpl = _TEMPLATES.get(col, col + " = {v}")
    try:
        return tmpl.format(v=v)
    except Exception:
        return f"{col} = {v}"


def top_reasons(X_row: pd.DataFrame, action: str, k: int = 3) -> list[dict]:
    """Return top-k POSITIVE SHAP contributors for p_cure under this action."""
    e = _explainer(action)
    sv = e.shap_values(X_row.astype(float))
    if isinstance(sv, list):     # multi-class returned list; take positive-class slice
        sv = sv[1] if len(sv) > 1 else sv[0]
    sv = np.asarray(sv)[0]
    out = []
    for i, col in enumerate(FEATURE_COLS):
        s = float(sv[i])
        if s > 0:
            out.append((s, col, X_row[col].iloc[0]))
    out.sort(key=lambda t: -t[0])
    reasons = []
    for s, col, v in out[:k]:
        reasons.append({"feature": col, "shap": round(s, 4), "value": None if pd.isna(v) else v,
                        "text": _format_val(col, v)})
    return reasons


def build_explanation(case_id: str, action: str, p_cure: float, dv: float, balance: float,
                      X_row: pd.DataFrame, allowed: dict, blocked_reasons: dict,
                      evidence_ids: dict | None = None) -> dict:
    """Full card for the Agent Desk."""
    r = top_reasons(X_row, action)
    return {
        "case_id": case_id,
        "recommended_action": action,
        "why_sentence": _ACTION_WHY.get(action, ""),
        "confidence_p_cure": round(float(p_cure), 3),
        "balance_at_risk": round(float(balance), 2),
        "decision_value": round(float(dv), 2),
        "top_reasons": r,
        "evidence": evidence_ids or {},
        "allowed_actions": allowed,
        "blocked_reasons": blocked_reasons,
    }
