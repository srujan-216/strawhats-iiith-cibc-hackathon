"""Agent Desk — Streamlit (read-only DuckDB).

  python run.py app      -> opens on port 8501

Screens (built in this order per the P7 plan):
  1. Case screen (C360 + NBA + SHAP + policy + Accept/Edit/Reject)   -- the demo
  2. Ask box (wraps QA.answer with the answer card)
  3. Role picker (agent / supervisor / manager)
  4. Supervisor queue (hardship + vulnerable + escalated + low confidence)
  5. Steward queue (silver.steward_queue)

Decisions log is append-only to warehouse/decisions.parquet. The app NEVER writes to DuckDB.
"""
from __future__ import annotations
import json, time, uuid
from pathlib import Path
import duckdb
import pandas as pd
import streamlit as st

from src.common.config import load_config
from src.layer4.nba import score_case, _load_models, _project, FEATURE_COLS
from src.layer4.explain import top_reasons

HERO_CASE = "CS-2026-134197"
DECISIONS_PARQUET = Path("warehouse/decisions.parquet")
REASON_CODES = [
    "accepted_as_is", "edited_action", "edited_timing", "customer_request",
    "agent_knowledge_overrides_model", "supervisor_override", "data_looks_wrong",
    "regulatory_concern", "other",
]


# --------------------------------------------------------------------------- cached accessors
@st.cache_resource
def _cfg(): return load_config()


@st.cache_resource
def _con():
    cfg = _cfg()
    return duckdb.connect(cfg["db_path"], read_only=True)


@st.cache_resource
def _models(): return _load_models()


@st.cache_data(ttl=60)
def fetch_case(case_id: str):
    con = _con()
    case = con.execute("""SELECT c.*, x.golden_id FROM silver.collections_cases c
        JOIN silver.id_xref x ON x.source_system='collections' AND x.source_key = c.case_id
        WHERE c.case_id = ?""", [case_id]).df()
    if case.empty: return None, None, None, None, None
    gid = case["golden_id"].iloc[0]
    cust = con.execute("SELECT * FROM gold.c360_customer WHERE golden_id = ?", [gid]).df()
    accts = con.execute("""SELECT * FROM gold.c360_account WHERE golden_id = ? ORDER BY role, source_system""", [gid]).df()
    contacts = con.execute("""SELECT ch.contact_ts_utc, ch.channel, ch.direction, ch.outcome_code,
                                    ch.sub_outcome_code, ch.contact_id
         FROM silver.contact_history ch
         JOIN silver.id_xref x ON x.source_system='crm' AND x.source_key = ch.crm_customer_id
         WHERE x.golden_id = ? ORDER BY ch.contact_ts_utc DESC LIMIT 30""", [gid]).df()
    notes = con.execute("""SELECT n.note_id, n.note_ts_utc, n.note_text, t.hardship, t.sentiment,
                                 t.ptp_mentioned, t.vulnerability_pred
         FROM silver.agent_notes n
         JOIN silver.id_xref x ON x.source_system='crm' AND x.source_key = n.crm_customer_id
         LEFT JOIN gold.text_features_notes t ON t.note_id = n.note_id
         WHERE x.golden_id = ? ORDER BY n.note_ts_utc DESC LIMIT 10""", [gid]).df()
    return case.iloc[0], cust.iloc[0] if not cust.empty else None, accts, contacts, notes


@st.cache_data(ttl=60)
def fetch_trust(gid: str):
    con = _con()
    return con.execute("SELECT field, source, refreshed_at, dq_status FROM gold.field_trust "
                       "WHERE golden_id = ? ORDER BY field", [gid]).df()


@st.cache_data(ttl=60)
def fetch_nba(case_id: str):
    con = _con()
    return con.execute("""SELECT * FROM gold.nba_recommendations WHERE case_id = ?""", [case_id]).df()


@st.cache_data(ttl=300)
def supervisor_queue(limit: int = 50):
    con = _con()
    return con.execute(f"""
        SELECT nba.case_id, nba.recommended_action, nba.p_cure::DOUBLE AS p_cure,
               nba.decision_value::DOUBLE AS decision_value, cc.current_bucket, cc.primary_product,
               cc.hardship_flag, cc.vulnerable_customer_flag,
               cc.insolvency_hold_flag, cc.deceased_hold_flag,
               nba.golden_id
          FROM gold.nba_recommendations nba
          JOIN silver.collections_cases cc ON cc.case_id = nba.case_id
         WHERE cc.case_status = 'open'
           AND (cc.hardship_flag OR cc.vulnerable_customer_flag
                OR nba.recommended_action = 'escalate'
                OR nba.p_cure::DOUBLE < 0.30)
         ORDER BY nba.decision_value::DOUBLE DESC
         LIMIT {int(limit)}""").df()


@st.cache_data(ttl=300)
def steward_queue(limit: int = 50):
    con = _con()
    try:
        return con.execute(f"SELECT * FROM silver.steward_queue ORDER BY match_probability DESC LIMIT {int(limit)}").df()
    except Exception:
        return pd.DataFrame()


# --------------------------------------------------------------------------- decisions log
def log_decision(case_id, golden_id, agent_role, action_taken, model_action, reason_code, note):
    row = pd.DataFrame([{"decision_id": str(uuid.uuid4()), "case_id": case_id, "golden_id": golden_id,
                          "agent_role": agent_role, "model_action": model_action,
                          "action_taken": action_taken, "reason_code": reason_code, "note": note,
                          "ts_utc": pd.Timestamp.utcnow().isoformat()}])
    DECISIONS_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    if DECISIONS_PARQUET.exists():
        old = pd.read_parquet(DECISIONS_PARQUET)
        row = pd.concat([old, row], ignore_index=True)
    row.to_parquet(DECISIONS_PARQUET, index=False)


# --------------------------------------------------------------------------- UI pieces
def _trust_dot(status):
    return {"ok": "🟢", "missing": "⚪", "invalid": "🔴", "stale": "🟡"}.get(status, "⚪")


def _render_case_screen(role: str, case_id: str):
    case, cust, accts, contacts, notes = fetch_case(case_id)
    if case is None:
        st.error(f"Case {case_id} not found"); return
    gid = case["golden_id"]
    nba_row = fetch_nba(case_id)
    trust = fetch_trust(gid)

    st.subheader(f"Case {case_id}  ·  golden_id {gid}  ·  {case['primary_product']}  ·  bucket {case['current_bucket']}")

    # ---- C360 strip
    with st.container(border=True):
        st.markdown("**Customer 360**")
        if cust is not None:
            cols = st.columns(5)
            cols[0].metric("Name", f"{cust['first_name']} {cust['last_name']}")
            cols[1].metric("Phone", str(cust["primary_phone_e164"] or "-"))
            cols[2].metric("Email", str(cust["email"] or "-"))
            cols[3].metric("Postal", str(cust["postal_code"] or "-"))
            cols[4].metric("Member records", f"{len(cust['member_crm_ids'])}")
            flags = []
            for col, label in [("deceased_any_source", "⚠ deceased"), ("insolvency_any_source", "⚠ insolvency"),
                                ("cease_contact_flag", "⚠ cease-contact"), ("vulnerability_flag", "🟣 vulnerable"),
                                ("has_deleted_member", "ℹ merged (incl. deleted CRM)")]:
                if bool(cust.get(col) or False): flags.append(label)
            if case["hardship_flag"]: flags.append("💙 hardship (case)")
            if flags:
                st.markdown(" · ".join(flags))

        # trust badges
        if not trust.empty:
            with st.expander(f"Trust badges ({len(trust)} fields)"):
                for _, t in trust.iterrows():
                    st.markdown(f"{_trust_dot(t['dq_status'])} **{t['field']}** – source: `{t['source']}`,"
                                 f" refreshed: {t['refreshed_at']}, status: {t['dq_status']}")

    # ---- NBA + reasons
    with st.container(border=True):
        st.markdown("**Next Best Action**")
        if nba_row.empty:
            st.info("No cached recommendation. Click 'Re-score live'.")
        else:
            r = nba_row.iloc[0]
            cols = st.columns(4)
            cols[0].metric("Recommended", str(r["recommended_action"]).replace("_", " "))
            cols[1].metric("p(cure)", f"{float(r['p_cure']):.1%}")
            cols[2].metric("Balance at risk", f"${float(r['balance_at_risk']):,.0f}")
            cols[3].metric("Decision value", f"${float(r['decision_value']):,.0f}")

        if st.button("Re-score live (score_case)", key=f"score_{case_id}"):
            with st.spinner("scoring..."):
                live = score_case(_cfg(), case_id, _models())
                st.session_state[f"live_{case_id}"] = live
        live = st.session_state.get(f"live_{case_id}")
        if live:
            st.caption(f"live latency: {live['latency_ms']} ms")
            # SHAP reasons for the recommended action
            try:
                con = _con()
                feats = con.execute("SELECT * FROM gold.features_online WHERE golden_id = ?", [gid]).df()
                X = _project(feats) if not feats.empty else pd.DataFrame({c: [0.0] for c in FEATURE_COLS})
                reasons = top_reasons(X, live["recommended_action"])
                st.markdown("**Top 3 reasons (SHAP)**")
                for r in reasons:
                    st.markdown(f"- {r['text']}  ·  shap +{r['shap']}")
            except Exception as e:
                st.caption(f"shap unavailable: {str(e)[:100]}")
            st.markdown("**Allowed actions**")
            for a, ok in live["allowed_actions"].items():
                reason = live.get("blocked_reasons", {}).get(a, "")
                st.markdown(f"- {'✅' if ok else '🚫'} {a}" + (f" — {reason}" if reason else ""))

    # ---- recent contacts and notes
    cL, cR = st.columns(2)
    with cL, st.container(border=True):
        st.markdown(f"**Recent contact history** ({len(contacts)} shown)")
        st.dataframe(contacts, hide_index=True, use_container_width=True)
    with cR, st.container(border=True):
        st.markdown(f"**Recent notes** ({len(notes)} shown)")
        for _, n in notes.iterrows():
            txt = n["note_text"] or "(placeholder)"
            tags = []
            if n.get("hardship") and n["hardship"] != "none": tags.append(f"hardship:{n['hardship']}")
            if n.get("sentiment"): tags.append(f"sentiment:{n['sentiment']}")
            if n.get("ptp_mentioned"): tags.append("PTP")
            if n.get("vulnerability_pred"): tags.append("vulnerable?")
            st.markdown(f"**{n['note_id']}** · {n['note_ts_utc']} · {' · '.join(tags)}\n\n> {txt[:200]}")

    # ---- Accept / Edit / Reject
    with st.container(border=True):
        st.markdown("**Decision**")
        if nba_row.empty:
            st.info("No recommendation to accept.")
            return
        rec = str(nba_row.iloc[0]["recommended_action"])
        c1, c2, c3 = st.columns(3)
        chosen = st.session_state.get(f"chosen_{case_id}", rec)
        edited = c2.selectbox("Edit action", ["no_contact", "digital_nudge", "call_best_time",
                                              "payment_plan", "hardship_referral", "escalate"],
                              index=["no_contact", "digital_nudge", "call_best_time", "payment_plan",
                                     "hardship_referral", "escalate"].index(rec),
                              key=f"edit_{case_id}")
        reason = c3.selectbox("Reason code", REASON_CODES, key=f"reason_{case_id}")
        note = st.text_input("Note (optional)", key=f"note_{case_id}")
        a, b, c = st.columns(3)
        if a.button("✅ Accept", key=f"accept_{case_id}"):
            log_decision(case_id, gid, role, rec, rec, "accepted_as_is", note)
            st.success(f"Accepted {rec} and logged.")
        if b.button("✏ Edit & submit", key=f"editsubmit_{case_id}"):
            log_decision(case_id, gid, role, edited, rec, reason, note)
            st.success(f"Logged action={edited} (reason={reason}).")
        if c.button("🚫 Reject", key=f"reject_{case_id}"):
            log_decision(case_id, gid, role, "none", rec, reason, note or "rejected")
            st.success(f"Rejected and logged (reason={reason}).")


def _render_ask_box():
    st.subheader("Ask the collections assistant")
    q = st.text_input("Question", key="qa_input")
    if st.button("Ask", key="qa_submit") and q.strip():
        from src.layer2.qa import QA
        with st.spinner("thinking..."):
            try:
                res = QA(_cfg()).answer(q)
            except Exception as e:
                st.error(f"gateway error: {e}")
                return
        badge = res.get("badge", "")
        colour = {"certified": "🟢", "exploratory": "🔵", "refused": "⚪"}.get(badge, "")
        st.markdown(f"**Answer** {colour} *{badge}*")
        st.markdown(res.get("answer", "(no answer)"))
        src = res.get("sql_or_sources", "")
        if src:
            with st.expander("SQL / sources"):
                st.code(src, language="sql" if "SELECT" in src.upper() else "text")
        if res.get("reasoning"):
            st.caption("Reasoning: " + res["reasoning"])


def _render_supervisor():
    st.subheader("Supervisor queue")
    df = supervisor_queue()
    st.caption(f"{len(df)} cases need supervisor attention (hardship, vulnerable, escalated, "
               f"or low p_cure)")
    st.dataframe(df, hide_index=True, use_container_width=True)


def _render_steward():
    st.subheader("Steward queue (identity matches 0.70-0.95)")
    df = steward_queue()
    st.caption(f"{len(df)} candidate pairs in the Splink steward band")
    st.dataframe(df, hide_index=True, use_container_width=True)


# --------------------------------------------------------------------------- main
def main():
    st.set_page_config(page_title="Agent Desk — Maple Collections", page_icon="💳", layout="wide")
    st.title("Agent Desk")
    with st.sidebar:
        role = st.selectbox("Role", ["agent", "supervisor", "manager"], key="role")
        screen = st.radio("Screen", ["Case", "Ask", "Supervisor queue", "Steward queue"], key="screen")
        case_id = st.text_input("Case id", value=st.session_state.get("case_id", HERO_CASE), key="case_id")
    if screen == "Case":
        _render_case_screen(role, case_id)
    elif screen == "Ask":
        _render_ask_box()
    elif screen == "Supervisor queue":
        _render_supervisor()
    elif screen == "Steward queue":
        _render_steward()


if __name__ == "__main__":
    main()
