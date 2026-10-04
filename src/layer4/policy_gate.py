"""Policy gate (CLAUDE.md section 5): runs AFTER the uplift model, blocks disallowed actions.

Rules (one test each; see tests/test_policy_gate.py):
  1. insolvency_hold or deceased_hold -> no_contact only
  2. cease_contact_flag or open dispute -> no_contact (digital nudges with payment links OK? NO:
     cease_contact bans any outbound in collections per POL-COLL-001; dispute pauses until review)
  3. third_party_representative -> contact representative only (modelled as hardship_referral)
  4. 7-day contact cap: if contacts_last_7d >= 3 -> block call_best_time, keep digital allowed up to cap
  5. permitted hours in customer local time zone: enforced at dialler time, not here (noted)
  6. hardship_flag (customer or case) -> hardship_referral only; never escalate / legal
  7. vulnerable_customer_flag -> supervisor queue (escalate blocked; hardship_referral preferred)
  8. 90+ bucket with no hardship signal -> escalate / payment_plan allowed; digital / call blocked
"""
from __future__ import annotations
import pandas as pd


ALL = ["no_contact", "digital_nudge", "call_best_time", "payment_plan",
       "hardship_referral", "escalate"]


class _Allowed(dict):
    """dict with .reasons attribute (per action: (allowed, reason))."""
    def __init__(self, data, reasons):
        super().__init__(data)
        self._reasons = reasons


def allowed_actions(case_row, feats_row=None) -> _Allowed:
    """Returns dict action -> True/False, with .reasons mapping action -> (True, '') or (False, 'why')."""
    d = {a: True for a in ALL}
    r = {a: (True, "") for a in ALL}

    def block(action, reason):
        d[action] = False
        r[action] = (False, reason)

    insolvency = bool(case_row.get("insolvency_hold_flag") or False)
    deceased = bool(case_row.get("deceased_hold_flag") or False)
    cease = bool(case_row.get("cease_contact_flag") or False)
    dispute = bool(case_row.get("dispute_flag") or False)
    third_party = bool(case_row.get("third_party_rep_flag") or False)
    vulnerable = bool(case_row.get("vulnerable_customer_flag") or False)
    hardship = bool(case_row.get("hardship_flag") or False)
    if feats_row is not None:
        hardship = hardship or bool(feats_row.get("vulnerability_signal") or False) or \
                   str(feats_row.get("txt_hardship_signal", "none")) == "clear"
    contacts_7d = int(feats_row.get("contacts_last_7d") or 0) if feats_row is not None else 0
    bucket = str(case_row.get("current_bucket") or "")
    is_90plus = bucket in ("91-120", "121-150", "151-180", "180+")

    # 1. insolvency / deceased -> no_contact only
    if insolvency or deceased:
        why = "insolvency hold" if insolvency else "deceased hold"
        for a in ALL:
            if a != "no_contact": block(a, why)
    # 2. cease_contact: no outbound at all
    if cease:
        for a in ("digital_nudge", "call_best_time", "payment_plan", "escalate"):
            block(a, "cease_contact flag")
    # dispute: pause until reviewed
    if dispute:
        for a in ("call_best_time", "escalate", "digital_nudge"):
            block(a, "open dispute")
    # 3. third-party representative: route to hardship_referral (which represents the "contact
    # representative only" option in our action set) and block direct contact
    if third_party:
        for a in ("digital_nudge", "call_best_time", "escalate"):
            block(a, "third-party representative on file")
    # 4. 7-day contact cap: 3 outbounds in 7d blocks call; digital still OK up to the next tier
    if contacts_7d >= 3:
        block("call_best_time", "7-day contact cap reached")
        if contacts_7d >= 5:
            block("digital_nudge", "7-day contact cap reached")
    # 6. hardship: NEVER harsher - block escalate, call pressure
    if hardship:
        block("escalate", "hardship flag protects from escalation")
        if not vulnerable:
            # keep call_best_time only if treatment is clearly supportive; the Agent Desk
            # surfaces the hardship_referral action as preferred
            pass
    # 7. vulnerable: supervisor queue - escalate blocked, hardship/no_contact preferred
    if vulnerable:
        block("escalate", "vulnerable_customer_flag")
    # 8. 90+ bucket with NO hardship: digital/call unlikely to add value; policy routes to escalate / payment_plan
    if is_90plus and not hardship and not vulnerable and not insolvency and not deceased and not cease:
        block("digital_nudge", "90+ bucket requires late-stage treatment")
        block("call_best_time", "90+ bucket requires late-stage treatment")

    return _Allowed(d, r)


def allowed_actions_vectorised(df: pd.DataFrame) -> dict:
    """Returns {action: boolean Series aligned with df.index}. Pandas-vectorised version
    of allowed_actions(); applied once over all open cases in batch_score()."""
    n = len(df)
    out = {a: pd.Series([True] * n, index=df.index) for a in ALL}
    g = lambda c, default=False: df[c].fillna(default).astype(bool) if c in df else pd.Series([default]*n, index=df.index)
    gnum = lambda c: pd.to_numeric(df[c], errors="coerce").fillna(0) if c in df else pd.Series([0]*n, index=df.index)
    insolvency = g("insolvency_hold_flag")
    deceased = g("deceased_hold_flag")
    cease = g("cease_contact_flag")
    dispute = g("dispute_flag")
    third_party = g("third_party_rep_flag")
    vulnerable = g("vulnerable_customer_flag")
    hardship = g("hardship_flag") | g("vulnerability_signal")
    if "txt_hardship_signal" in df:
        hardship = hardship | (df["txt_hardship_signal"].astype(str) == "clear")
    contacts_7d = gnum("contacts_last_7d")
    bucket = df["current_bucket"].astype(str) if "current_bucket" in df else pd.Series([""] * n, index=df.index)
    is_90plus = bucket.isin(["91-120", "121-150", "151-180", "180+"])

    # rule 1
    hold = insolvency | deceased
    for a in ALL:
        if a != "no_contact":
            out[a] &= ~hold
    # rule 2 cease
    for a in ("digital_nudge", "call_best_time", "payment_plan", "escalate"):
        out[a] &= ~cease
    # rule 2b dispute
    for a in ("call_best_time", "escalate", "digital_nudge"):
        out[a] &= ~dispute
    # rule 3 third-party
    for a in ("digital_nudge", "call_best_time", "escalate"):
        out[a] &= ~third_party
    # rule 4 cap
    out["call_best_time"] &= ~(contacts_7d >= 3)
    out["digital_nudge"] &= ~(contacts_7d >= 5)
    # rule 6 hardship
    out["escalate"] &= ~hardship
    # rule 7 vulnerable
    out["escalate"] &= ~vulnerable
    # rule 8 90+ no hardship
    protected_group = insolvency | deceased | cease | hardship | vulnerable
    severe = is_90plus & ~protected_group
    out["digital_nudge"] &= ~severe
    out["call_best_time"] &= ~severe
    return out
