"""Layer 3: numeric and text-derived features.

  python run.py features                 # build gold.features_offline + gold.features_online
  python run.py features --sample N      # just the N customers from the shared sample helper

A feature catalog entry (src/layer3/catalog.yaml) lives next to a SQL template below. Both the
offline (point-in-time, by decision_date) and online (latest snapshot) paths use the SAME SQL
expression per feature, parameterised on :as_of. A parity test (tests/test_feature_parity.py)
compares the two outputs on 1,000 random golden_ids and must match to the last decimal.

For the hackathon the only live decision_date is SNAPSHOT_DATE (2026-09-28). The offline path
accepts a list of decision_dates for later retraining; the SQL below filters contact_history and
promises_to_pay by ts < as_of, so historical dates work if the latest-snapshot assumption is
relaxed (not needed for the demo).

Text features are produced by src/layer3/text_classifier.py and stored in
gold.text_features_notes / gold.text_features_transcripts; this module aggregates them per
customer and merges them into features_offline/online.
"""
from __future__ import annotations
import time
from pathlib import Path
import duckdb
import yaml
from src.common.sample import build_sample, sample_filter

SNAPSHOT_DATE = "2026-09-28"

# ----------------------------------------------------------------------------- numeric features
# Each entry is a CTE: (name, SQL). Must produce (golden_id, <columns>). The last column list
# in NUMERIC_COLUMNS below is the output schema.
NUMERIC_FEATURE_CTES = [
    # ---- account-based: dpd + utilisation + balance at risk ----
    ("feat_account", """
        SELECT ca.golden_id,
               max(ca.dpd) AS dpd_level,
               max(ca.worst_dpd_12m) AS worst_dpd_12m,
               sum(CASE WHEN ca.dpd > 0 THEN ca.current_balance ELSE 0 END) AS balance_at_risk
          FROM gold.c360_account ca WHERE ca.role = 'primary'
         GROUP BY ca.golden_id"""),
    # dpd 3-month slope from card dpd_m columns (cards only; loans do not expose month-by-month)
    ("feat_dpd_slope", """
        SELECT a.golden_id,
               max(ca.dpd) - max(ca.dpd_m03) AS dpd_slope_3m
          FROM silver.card_accounts ca
          JOIN gold.c360_account a ON a.source_system = 'cards' AND a.account_id = ca.card_account_id
                                  AND a.role = 'primary'
         GROUP BY a.golden_id"""),
    # card utilisation now vs 6 months ago (card_statements has history; use closing_balance/credit_limit)
    ("feat_util_trend", """
        WITH now_stmt AS (
            SELECT cs.card_account_id,
                   closing_balance / nullif(credit_limit_at_statement, 0) AS u
              FROM main.card_statements cs
             WHERE cs.statement_date = (SELECT max(statement_date) FROM main.card_statements s
                                          WHERE s.card_account_id = cs.card_account_id)),
        then_stmt AS (
            SELECT cs.card_account_id,
                   closing_balance / nullif(credit_limit_at_statement, 0) AS u
              FROM main.card_statements cs
             WHERE cs.cycle_no = (SELECT max(cycle_no) - 6 FROM main.card_statements s
                                    WHERE s.card_account_id = cs.card_account_id))
        SELECT a.golden_id,
               avg(coalesce(n.u, 0) - coalesce(t.u, 0)) AS utilisation_trend_6m
          FROM gold.c360_account a
          LEFT JOIN now_stmt n ON n.card_account_id = a.account_id
          LEFT JOIN then_stmt t ON t.card_account_id = a.account_id
         WHERE a.source_system = 'cards' AND a.role = 'primary'
         GROUP BY a.golden_id"""),

    # ---- promises ----
    ("feat_promises", """
        SELECT xc.golden_id,
               count(*) FILTER (WHERE p.ptp_status = 'broken' AND p.status_ts >= :as_of::DATE - INTERVAL 90 DAY
                                                                AND p.status_ts <  :as_of::DATE + INTERVAL 1 DAY)
                   AS broken_promises_90d
          FROM silver.promises_to_pay p
          JOIN silver.id_xref xc ON xc.source_system = 'crm' AND xc.source_key = p.crm_customer_id
         GROUP BY xc.golden_id"""),
    ("feat_promise_gap", """
        SELECT xc.golden_id,
               median(datediff('day', da.expected_next_payroll_date, p.ptp_due_date)) AS promise_due_vs_payday_gap_days
          FROM silver.promises_to_pay p
          JOIN silver.id_xref xc ON xc.source_system = 'crm' AND xc.source_key = p.crm_customer_id
          JOIN gold.c360_account a ON a.golden_id = xc.golden_id AND a.source_system = 'deposits'
          JOIN silver.deposit_accounts da ON da.deposit_account_id = a.account_id
         WHERE p.ptp_due_date IS NOT NULL AND da.expected_next_payroll_date IS NOT NULL
           AND p.ptp_created_ts >= :as_of::DATE - INTERVAL 90 DAY
         GROUP BY xc.golden_id"""),

    # ---- deposit cash flow ----
    ("feat_deposit", """
        SELECT a.golden_id,
               max(da.payroll_delay_days) AS payroll_delay_days,
               avg(da.payroll_amount_change_pct) AS salary_change_3m_pct,
               sum(coalesce(da.nsf_count_mtd, 0)) AS nsf_count_3m,
               -- direction (sign of latest cash flow) scaled by 6m volatility: positive = resilient
               avg(CASE WHEN abs(da.net_cash_flow_mtd) > 0
                        THEN sign(da.net_cash_flow_mtd) * coalesce(da.cash_flow_volatility_6m, 0)
                        ELSE 0 END) AS cash_flow_slope_6m
          FROM silver.deposit_accounts da
          JOIN gold.c360_account a ON a.source_system = 'deposits' AND a.account_id = da.deposit_account_id
                                   AND a.role = 'primary'
         GROUP BY a.golden_id"""),

    # ---- bureau (nullable; NULL for ~52% of customers; see catalog) ----
    ("feat_bureau", """
        SELECT golden_id,
               (bureau_risk_score IS NOT NULL)::BOOLEAN AS bureau_present,
               -- risk_score_delta_90d not kept in c360_customer; refetch from silver.external
               NULL::INTEGER AS bureau_delta_90d_placeholder
          FROM gold.c360_customer"""),
    ("feat_bureau_delta", """
        WITH latest AS (
            SELECT ams.crm_customer_id, e.risk_score_delta_90d, e.pull_date,
                   row_number() OVER (PARTITION BY ams.crm_customer_id ORDER BY e.pull_date DESC) rn
              FROM main.account_monthly_snapshot ams
              JOIN silver.deposit_accounts d ON d.deposit_account_id = ams.account_id
              JOIN silver.external e ON e.bank_subject_ref = d.src_customer_ref
             WHERE NOT list_contains(e.dq_flags, 'repaired_DFI0812'))
        SELECT x.golden_id, max(l.risk_score_delta_90d) AS bureau_delta_90d
          FROM latest l
          JOIN silver.id_xref x ON x.source_system = 'crm' AND x.source_key = l.crm_customer_id
         WHERE l.rn = 1
         GROUP BY x.golden_id"""),

    # ---- contact behaviour ----
    ("feat_contact", """
        WITH ch AS (
            SELECT xc.golden_id, c.outcome_code, c.contact_ts_utc, c.channel, c.direction
              FROM silver.contact_history c
              JOIN silver.id_xref xc ON xc.source_system = 'crm' AND xc.source_key = c.crm_customer_id
             WHERE c.contact_ts_utc < :as_of::DATE + INTERVAL 1 DAY),
        rpc_codes AS (SELECT code FROM main.code_lookups
                       WHERE code_type = 'outcome_code' AND json_extract(attributes_json, '$.counts_as_rpc') = 'true')
        SELECT golden_id,
               count(*) FILTER (WHERE direction = 'outbound'
                                 AND contact_ts_utc >= :as_of::DATE - INTERVAL 7 DAY) AS contacts_last_7d,
               nullif(count(*) FILTER (WHERE direction = 'outbound' AND channel = 'call'
                                        AND contact_ts_utc >= :as_of::DATE - INTERVAL 30 DAY), 0) AS calls_30d,
               count(*) FILTER (WHERE direction = 'outbound' AND channel = 'call'
                                 AND contact_ts_utc >= :as_of::DATE - INTERVAL 30 DAY
                                 AND outcome_code IN (SELECT code FROM rpc_codes)) AS rpc_30d
          FROM ch GROUP BY golden_id"""),
    # best time band: hour with highest RPC rate in last 90d call history
    ("feat_best_time", """
        WITH h AS (
            SELECT xc.golden_id, hour(c.contact_ts_utc) AS hr,
                   count(*) AS calls,
                   count(*) FILTER (WHERE c.outcome_code IN (
                       SELECT code FROM main.code_lookups
                        WHERE code_type='outcome_code' AND json_extract(attributes_json,'$.counts_as_rpc')='true')) AS rpc
              FROM silver.contact_history c
              JOIN silver.id_xref xc ON xc.source_system='crm' AND xc.source_key = c.crm_customer_id
             WHERE c.direction='outbound' AND c.channel='call'
               AND c.contact_ts_utc >= :as_of::DATE - INTERVAL 90 DAY
               AND c.contact_ts_utc <  :as_of::DATE + INTERVAL 1 DAY
             GROUP BY xc.golden_id, hour(c.contact_ts_utc)
            HAVING count(*) >= 3)
        SELECT golden_id,
               (array_agg(hr ORDER BY rpc * 1.0 / nullif(calls, 0) DESC, hr ASC))[1] AS best_time_band_hour
          FROM h GROUP BY golden_id"""),
    # ---- text features per customer, from gold.text_features_* (built by text_classifier.py) ----
    # "clear" wins over "possible" wins over "none"; latest 90-day texts only
    ("feat_text", """
        WITH note_x AS (
            SELECT xc.golden_id, t.hardship, t.delay_reason, t.ptp_mentioned, t.ptp_intent_strength,
                   t.sentiment, t.vulnerability_pred, t.vulnerability_conf, t.dispute_mention,
                   n.note_ts_utc AS ts
              FROM gold.text_features_notes t
              JOIN silver.agent_notes n ON n.note_id = t.note_id
              JOIN silver.id_xref xc ON xc.source_system='crm' AND xc.source_key = n.crm_customer_id
             WHERE n.note_ts_utc >= :as_of::DATE - INTERVAL 90 DAY
               AND n.note_ts_utc <  :as_of::DATE + INTERVAL 1 DAY),
        tr_x AS (
            SELECT xc.golden_id, t.hardship, t.delay_reason, t.ptp_mentioned, t.ptp_intent_strength,
                   t.sentiment, t.vulnerability_pred, t.vulnerability_conf, t.dispute_mention,
                   ct.call_start_ts AS ts
              FROM gold.text_features_transcripts t
              JOIN main.call_transcripts ct ON CAST(ct.transcript_id AS VARCHAR) = t.transcript_id
              JOIN silver.id_xref xc ON xc.source_system='crm' AND xc.source_key = ct.crm_customer_id
             WHERE ct.call_start_ts >= :as_of::DATE - INTERVAL 90 DAY
               AND ct.call_start_ts <  :as_of::DATE + INTERVAL 1 DAY),
        all_text AS (SELECT * FROM note_x UNION ALL SELECT * FROM tr_x)
        SELECT golden_id,
               -- hardship: argmax by severity rank
               (array_agg(hardship ORDER BY CASE hardship WHEN 'clear' THEN 3 WHEN 'possible' THEN 2
                                                           WHEN 'none' THEN 1 ELSE 0 END DESC, ts DESC))[1]
                   AS txt_hardship_signal,
               -- delay reason: most recent non-unknown
               coalesce(
                   (array_agg(delay_reason ORDER BY ts DESC) FILTER (WHERE delay_reason <> 'unknown'))[1],
                   'unknown') AS txt_delay_reason,
               bool_or(ptp_mentioned) AS txt_ptp_mentioned,
               max(ptp_intent_strength) FILTER (WHERE ptp_mentioned) AS txt_ptp_intent_strength,
               -- sentiment: most-recent-wins
               (array_agg(sentiment ORDER BY ts DESC))[1] AS txt_sentiment,
               -- vulnerability: classifier tipping to true only when conf > 0.8
               bool_or(vulnerability_pred AND vulnerability_conf > 0.8) AS txt_vulnerability_tip,
               bool_or(dispute_mention) AS txt_dispute_mention
          FROM all_text GROUP BY golden_id"""),
]

NUMERIC_COLUMNS = [
    "dpd_level", "worst_dpd_12m", "dpd_slope_3m",
    "utilisation_trend_6m", "balance_at_risk",
    "broken_promises_90d", "promise_due_vs_payday_gap_days",
    "payroll_delay_days", "salary_change_3m_pct", "nsf_count_3m", "cash_flow_slope_6m",
    "bureau_present", "bureau_delta_90d",
    "contacts_last_7d", "answer_rate_30d", "best_time_band_hour",
]
TEXT_COLUMNS = [
    "txt_hardship_signal", "txt_delay_reason", "txt_ptp_mentioned",
    "txt_ptp_intent_strength", "txt_sentiment", "vulnerability_signal",
    "txt_dispute_mention",
]
NUMERIC_DEFAULTS = {   # from catalog "default_on_null" where set
    "dpd_level": 0, "worst_dpd_12m": 0, "dpd_slope_3m": 0, "balance_at_risk": 0.0,
    "broken_promises_90d": 0, "payroll_delay_days": 0, "nsf_count_3m": 0,
    "bureau_present": False, "contacts_last_7d": 0,
}


def _assemble_sql(as_of: str, sample_n: int | None) -> str:
    """Join all feature CTEs onto gold.c360_customer; derive answer_rate_30d from the contact CTE."""
    # restrict customers to the sample via silver.id_xref (crm source_key -> golden_id)
    sample_join = ("JOIN silver.id_xref x ON x.source_system='crm' AND x.golden_id = c.golden_id "
                   "AND x.source_key IN (SELECT crm_customer_id FROM sample_crm)") if sample_n else ""
    ctes = ",\n".join(f"{name} AS ({sql.replace(':as_of', repr(as_of))})" for name, sql in NUMERIC_FEATURE_CTES)
    return f"""
WITH {ctes},
customers AS (
    SELECT DISTINCT c.golden_id, DATE '{as_of}' AS decision_date
      FROM gold.c360_customer c {sample_join})
SELECT c.golden_id, c.decision_date,
       coalesce(a.dpd_level, 0)                  AS dpd_level,
       coalesce(a.worst_dpd_12m, 0)              AS worst_dpd_12m,
       coalesce(d.dpd_slope_3m, 0)               AS dpd_slope_3m,
       u.utilisation_trend_6m                    AS utilisation_trend_6m,
       coalesce(a.balance_at_risk, 0)            AS balance_at_risk,
       coalesce(p.broken_promises_90d, 0)        AS broken_promises_90d,
       g.promise_due_vs_payday_gap_days          AS promise_due_vs_payday_gap_days,
       coalesce(dep.payroll_delay_days, 0)       AS payroll_delay_days,
       dep.salary_change_3m_pct                  AS salary_change_3m_pct,
       coalesce(dep.nsf_count_3m, 0)             AS nsf_count_3m,
       dep.cash_flow_slope_6m                    AS cash_flow_slope_6m,
       coalesce(b.bureau_present, false)         AS bureau_present,
       bd.bureau_delta_90d                       AS bureau_delta_90d,
       coalesce(ct.contacts_last_7d, 0)          AS contacts_last_7d,
       ct.rpc_30d::DOUBLE / nullif(ct.calls_30d, 0) AS answer_rate_30d,
       bt.best_time_band_hour                    AS best_time_band_hour,
       -- text features (NULL if the customer has no notes/transcripts in last 90d)
       coalesce(tx.txt_hardship_signal, 'none')  AS txt_hardship_signal,
       coalesce(tx.txt_delay_reason, 'unknown')  AS txt_delay_reason,
       coalesce(tx.txt_ptp_mentioned, false)     AS txt_ptp_mentioned,
       tx.txt_ptp_intent_strength                AS txt_ptp_intent_strength,
       coalesce(tx.txt_sentiment, 'neutral')     AS txt_sentiment,
       -- vulnerability_signal: structured OR tip; classifier can only flip to TRUE
       (coalesce(cv.vulnerability_flag, false)
        OR coalesce(tx.txt_vulnerability_tip, false)) AS vulnerability_signal,
       coalesce(tx.txt_dispute_mention, false)   AS txt_dispute_mention
  FROM customers c
  LEFT JOIN feat_account    a   ON a.golden_id = c.golden_id
  LEFT JOIN feat_dpd_slope  d   ON d.golden_id = c.golden_id
  LEFT JOIN feat_util_trend u   ON u.golden_id = c.golden_id
  LEFT JOIN feat_promises   p   ON p.golden_id = c.golden_id
  LEFT JOIN feat_promise_gap g  ON g.golden_id = c.golden_id
  LEFT JOIN feat_deposit    dep ON dep.golden_id = c.golden_id
  LEFT JOIN feat_bureau     b   ON b.golden_id = c.golden_id
  LEFT JOIN feat_bureau_delta bd ON bd.golden_id = c.golden_id
  LEFT JOIN feat_contact    ct  ON ct.golden_id = c.golden_id
  LEFT JOIN feat_best_time  bt  ON bt.golden_id = c.golden_id
  LEFT JOIN feat_text       tx  ON tx.golden_id = c.golden_id
  -- vulnerability survivorship: carried from c360_customer (OR across source CRM records)
  LEFT JOIN (SELECT golden_id, vulnerability_flag FROM gold.c360_customer) cv ON cv.golden_id = c.golden_id
"""


# ------------------------------------------------------------------------------- orchestrator
def _ensure_gold_schema(con):
    con.execute("CREATE SCHEMA IF NOT EXISTS gold")


def build_offline(cfg: dict, decision_dates: list[str] | None = None,
                  sample_n: int | None = None, log=print) -> dict:
    """Build gold.features_offline keyed by (golden_id, decision_date). Default: single as_of = SNAPSHOT_DATE."""
    dates = decision_dates or [SNAPSHOT_DATE]
    con = duckdb.connect(cfg["db_path"])
    scfg = cfg.get("silver", {})
    con.execute(f"SET memory_limit='{scfg.get('memory_limit', '4GB')}'; "
                f"SET threads={int(scfg.get('threads', 4))}; SET preserve_insertion_order=false;")
    _ensure_gold_schema(con)
    if sample_n:
        build_sample(con, sample_n, log=log)
    con.execute("DROP TABLE IF EXISTS gold.features_offline")
    first = True
    n_total = 0
    t0 = time.time()
    for d in dates:
        sql = _assemble_sql(d, sample_n)
        if first:
            con.execute(f"CREATE TABLE gold.features_offline AS {sql}")
            first = False
        else:
            con.execute(f"INSERT INTO gold.features_offline {sql}")
        n = con.execute("SELECT count(*) FROM gold.features_offline WHERE decision_date = ?",
                        [d]).fetchone()[0]
        log(f"  features_offline for {d}: {n:,} rows")
        n_total += n
    con.execute(f"CREATE OR REPLACE TABLE gold.features_online AS "
                f"SELECT * EXCLUDE (decision_date), now() AS refreshed_at "
                f"FROM gold.features_offline WHERE decision_date = DATE '{dates[-1]}'")
    log(f"  features_online: {con.execute('SELECT count(*) FROM gold.features_online').fetchone()[0]:,} rows "
        f"({time.time()-t0:.1f}s total)")
    con.close()
    return {"offline_rows": n_total, "online_rows": n, "columns": NUMERIC_COLUMNS}


def get_online(cfg: dict, golden_ids: list[str]) -> list[dict]:
    """Point lookup for Layer 4 scoring."""
    con = duckdb.connect(cfg["db_path"], read_only=True)
    try:
        q = ("SELECT * FROM gold.features_online WHERE golden_id IN ("
             + ",".join("?" for _ in golden_ids) + ")")
        rows = con.execute(q, list(golden_ids)).fetchall()
        cols = [c[0] for c in con.description]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        con.close()


def load_catalog() -> dict:
    return yaml.safe_load(Path(__file__).parent.joinpath("catalog.yaml").read_text(encoding="utf-8"))
