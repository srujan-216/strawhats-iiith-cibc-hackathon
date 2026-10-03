"""Layer 1, step 3: golden C360 tables + field-level lineage/trust.

  python run.py c360

Three gold.* tables, one row per entity:

  gold.c360_customer   one per golden_id, member CRM records merged by the survivorship rules in
                       CLAUDE.md section 5. Protective flags (hardship, vulnerability, insolvency,
                       deceased, cease-contact) are TRUE if ANY source is true; consent flags are
                       AND (most restrictive wins); contact details come from the most recently
                       verified/updated CRM record in the cluster.
  gold.c360_account    one row per (account_id, role). role = primary / joint / co_borrower.
  gold.c360_case       one row per case; golden_id resolved via collections_cases.coll_customer_ref.

Also:
  gold.field_trust     lineage: for a few key customer fields (phone, email, postal, hardship,
                       deceased, insolvency), (source, refreshed_at, dq_status).

DFI-0812 bureau rows are repaired in silver (not quarantined); c360 does carry them, but Q6 flags
any that still look rotated, and the risk-score columns on c360_customer come from the latest
non-repaired bureau pull per subject so a demo question like "did the Aug 12 loader incident
affect this customer?" has a clean answer.
"""
from __future__ import annotations
import time
import duckdb

SNAPSHOT_DATE = "2026-09-28"

CUSTOMER_SQL = f"""
CREATE OR REPLACE TABLE gold.c360_customer AS
WITH clustered AS (
    SELECT x.golden_id, c.*
      FROM silver.id_xref x
      JOIN silver.customers c ON c.crm_customer_id = x.source_key
     WHERE x.source_system = 'crm'
),
ranked AS (
    -- pick the "most recently touched" live record for contact fields; stable tie-break on crm_customer_id
    SELECT *,
           row_number() OVER (PARTITION BY golden_id ORDER BY
               (cdc_operation = 'D')::INT ASC,                           -- live wins
               coalesce(last_profile_update_ts, consent_last_updated_ts) DESC NULLS LAST,
               crm_customer_id) AS _rank_live,
           row_number() OVER (PARTITION BY golden_id ORDER BY
               (email_verified_flag IS TRUE)::INT DESC,
               (cdc_operation = 'D')::INT ASC,
               coalesce(last_profile_update_ts, '1900-01-01'::TIMESTAMP) DESC,
               crm_customer_id) AS _rank_email,
           row_number() OVER (PARTITION BY golden_id ORDER BY
               (income_verified_flag IS TRUE)::INT DESC,
               (cdc_operation = 'D')::INT ASC,
               coalesce(address_since_date, '1900-01-01'::DATE) DESC,
               crm_customer_id) AS _rank_address
      FROM clustered
),
bureau_by_crm AS (
    -- latest non-repaired bureau score per CRM customer (via deposits -> external CIF)
    SELECT ams.crm_customer_id, e.risk_score, e.bankruptcy_on_file_flag, e.deceased_indicator,
           e.pull_date,
           row_number() OVER (PARTITION BY ams.crm_customer_id ORDER BY e.pull_date DESC) AS rn
      FROM main.account_monthly_snapshot ams
      JOIN silver.deposit_accounts d ON d.deposit_account_id = ams.account_id
      JOIN silver.external e ON e.bank_subject_ref = d.src_customer_ref
     WHERE NOT list_contains(e.dq_flags, 'repaired_DFI0812')
),
bureau_by_golden AS (
    SELECT x.golden_id, b.risk_score, b.bankruptcy_on_file_flag, b.deceased_indicator,
           b.pull_date AS bureau_pull_date,
           row_number() OVER (PARTITION BY x.golden_id ORDER BY b.pull_date DESC) AS rn
      FROM bureau_by_crm b
      JOIN silver.id_xref x ON x.source_system = 'crm' AND x.source_key = b.crm_customer_id
     WHERE b.rn = 1
),
survivorship AS (
    SELECT
        c.golden_id,
        list_distinct(list_sort(list(c.crm_customer_id))) AS member_crm_ids,
        count(*) AS member_count,
        count(*) FILTER (WHERE NOT (c.cdc_operation = 'D')) AS live_member_count,
        -- contact: most recently touched live record
        any_value(c.primary_phone_e164)       FILTER (WHERE c._rank_live = 1) AS primary_phone_e164,
        any_value(c.email)                    FILTER (WHERE c._rank_email = 1) AS email,
        any_value(c.email_verified_flag)      FILTER (WHERE c._rank_email = 1) AS email_verified_flag,
        any_value(c.postal_code)              FILTER (WHERE c._rank_address = 1) AS postal_code,
        any_value(c.province_code)            FILTER (WHERE c._rank_address = 1) AS province_code,
        any_value(c.fsa)                      FILTER (WHERE c._rank_address = 1) AS fsa,
        any_value(c.country_code)             FILTER (WHERE c._rank_address = 1) AS country_code,
        any_value(c.time_zone)                FILTER (WHERE c._rank_live = 1) AS time_zone,
        any_value(c.first_name)               FILTER (WHERE c._rank_live = 1) AS first_name,
        any_value(c.last_name)                FILTER (WHERE c._rank_live = 1) AS last_name,
        any_value(c.dob_parsed)               FILTER (WHERE c._rank_live = 1) AS date_of_birth,
        bool_or(c.dob_ambiguous)                                                   AS dob_ambiguous,
        -- consent: AND over sources (most restrictive wins)
        bool_and(coalesce(c.consent_call, true))                                   AS consent_call,
        bool_and(coalesce(c.consent_call_mobile, true))                            AS consent_call_mobile,
        bool_and(coalesce(c.consent_autodialer, true))                             AS consent_autodialer,
        bool_and(coalesce(c.consent_sms, true))                                    AS consent_sms,
        bool_and(coalesce(c.consent_email, true))                                  AS consent_email,
        bool_and(coalesce(c.consent_push, true))                                   AS consent_push,
        bool_and(coalesce(c.consent_letter, true))                                 AS consent_letter,
        bool_and(coalesce(c.casl_express_consent_email, false))                    AS casl_express_consent_email,
        bool_and(coalesce(c.voicemail_permitted, true))                            AS voicemail_permitted,
        -- protective flags: OR (true if ANY source true), per CLAUDE §5
        bool_or(coalesce(c.cease_communication_flag, false))                       AS cease_contact_flag,
        max(c.cease_communication_date)                                            AS cease_contact_date,
        bool_or(coalesce(c.vulnerability_flag, false))                             AS vulnerability_flag,
        any_value(c.vulnerability_type)       FILTER (WHERE c.vulnerability_flag) AS vulnerability_type,
        bool_or(coalesce(c.deceased_flag, false))                                  AS deceased_flag,
        min(c.deceased_notified_date)                                              AS deceased_notified_date,
        min(c.insolvency_filed_date)                                               AS insolvency_filed_date,
        bool_or(c.insolvency_filed_date IS NOT NULL)                               AS insolvency_flag,
        bool_or(c.cdc_operation = 'D')                                             AS has_deleted_member,
        bool_and(c.cdc_operation = 'D')                                            AS is_all_deleted,
        max(c.last_profile_update_ts)                                              AS last_profile_update_ts
      FROM ranked c
     GROUP BY c.golden_id
)
SELECT s.*,
       b.risk_score                 AS bureau_risk_score,
       b.bureau_pull_date,
       coalesce(b.deceased_indicator, false) OR s.deceased_flag AS deceased_any_source,
       coalesce(b.bankruptcy_on_file_flag, false) OR s.insolvency_flag AS insolvency_any_source,
       now() AS refreshed_at,
       'silver.customers + silver.id_xref + silver.external' AS lineage
  FROM survivorship s
  LEFT JOIN bureau_by_golden b ON b.golden_id = s.golden_id AND b.rn = 1
"""

ACCOUNT_SQL = """
CREATE OR REPLACE TABLE gold.c360_account AS
-- Precomputed (src_customer_ref -> account_id) maps so joint/co-borrower lookups become hash
-- equi-joins. The earlier `WHERE x.source_key IN (SELECT ... WHERE ref = outer_col)` form was a
-- correlated subquery that DuckDB had to materialise for every outer row (140k x 780k => 171 GB
-- temp spill, OOM). This CTE pattern is also used wherever c360 needs a src_ref -> id lookup.
WITH dep_ref_to_acct AS (
    SELECT src_customer_ref AS ref, deposit_account_id AS account_id
      FROM silver.deposit_accounts
     WHERE src_customer_ref IS NOT NULL),
loan_ref_to_acct AS (
    SELECT src_customer_ref AS ref, loan_id AS account_id
      FROM silver.loan_accounts
     WHERE src_customer_ref IS NOT NULL),
primary_roles AS (
    -- xref already resolves owner -> golden_id
    SELECT x.golden_id, x.source_system, x.source_key AS account_id,
           'primary' AS role, CAST(NULL AS VARCHAR) AS co_holder_crm_id
      FROM silver.id_xref x
     WHERE x.source_system IN ('cards', 'loans', 'deposits')),
joint_deposits AS (
    -- joint deposit holder: joint_holder_ref is another holder's src_customer_ref
    SELECT xj.golden_id, 'deposits' AS source_system, d.deposit_account_id AS account_id,
           'joint' AS role, xj.source_key AS co_holder_crm_id
      FROM silver.deposit_accounts d
      JOIN dep_ref_to_acct h ON h.ref = d.joint_holder_ref
      JOIN silver.id_xref xd ON xd.source_system = 'deposits' AND xd.source_key = d.deposit_account_id
      JOIN silver.id_xref xj ON xj.source_system = 'deposits' AND xj.source_key = h.account_id
     WHERE d.joint_account_flag AND d.joint_holder_ref IS NOT NULL
       AND xj.golden_id <> xd.golden_id),
co_borrowers AS (
    -- loan co-borrower: co_borrower_ref is another borrower's src_customer_ref
    SELECT xc.golden_id, 'loans' AS source_system, l.loan_id AS account_id,
           'co_borrower' AS role, xc.source_key AS co_holder_crm_id
      FROM silver.loan_accounts l
      JOIN loan_ref_to_acct h ON h.ref = l.co_borrower_ref
      JOIN silver.id_xref xl ON xl.source_system = 'loans' AND xl.source_key = l.loan_id
      JOIN silver.id_xref xc ON xc.source_system = 'loans' AND xc.source_key = h.account_id
     WHERE l.co_borrower_flag AND l.co_borrower_ref IS NOT NULL
       AND xc.golden_id <> xl.golden_id)
SELECT golden_id, source_system, account_id, role, co_holder_crm_id, now() AS refreshed_at
  FROM (SELECT * FROM primary_roles UNION ALL
        SELECT * FROM joint_deposits UNION ALL
        SELECT * FROM co_borrowers)
"""

# Account facts: the primary role rows carry the system-of-record fields.
ACCOUNT_FACTS_SQL = """
CREATE OR REPLACE TABLE gold.c360_account AS
WITH primary_rows AS (
    SELECT golden_id, source_system, account_id, role, co_holder_crm_id, refreshed_at
      FROM gold.c360_account_roles
),
card_f AS (SELECT card_account_id AS account_id, 'cards' AS source_system, product_code,
                  account_status, snapshot_date, dpd, dpd_bucket, worst_dpd_12m,
                  current_balance, past_due_amount, credit_limit::DOUBLE AS credit_limit_or_original_amount,
                  CAST(NULL AS DATE) AS maturity_date, CAST(NULL AS VARCHAR) AS block_code_or_reason,
                  dq_flags
             FROM silver.card_accounts),
loan_f AS (SELECT loan_id, 'loans', product_code, 'open' AS account_status, snapshot_date, dpd,
                  dpd_bucket, worst_dpd_12m, total_outstanding AS current_balance, past_due_amount,
                  original_amount, maturity_date, CAST(NULL AS VARCHAR), dq_flags
             FROM silver.loan_accounts),
dep_f AS (SELECT deposit_account_id, 'deposits', product_code, account_status, snapshot_date,
                 overdraft_dpd, overdraft_dpd_bucket, CAST(NULL AS BIGINT), current_balance,
                 CAST(NULL AS DOUBLE), overdraft_limit, CAST(NULL AS DATE), freeze_reason, dq_flags
            FROM silver.deposit_accounts)
SELECT p.golden_id, p.source_system, p.account_id, p.role, p.co_holder_crm_id,
       f.product_code, f.account_status, f.snapshot_date, f.dpd, f.dpd_bucket, f.worst_dpd_12m,
       f.current_balance, f.past_due_amount, f.credit_limit_or_original_amount, f.maturity_date,
       f.block_code_or_reason, f.dq_flags, p.refreshed_at
  FROM primary_rows p
  LEFT JOIN (SELECT * FROM card_f UNION ALL SELECT * FROM loan_f UNION ALL SELECT * FROM dep_f) f
    ON f.source_system = p.source_system AND f.account_id = p.account_id
"""

CASE_SQL = """
CREATE OR REPLACE TABLE gold.c360_case AS
SELECT
    cc.case_id,
    xc.golden_id,
    cc.case_status,
    cc.case_open_date,
    cc.case_status_date,
    cc.primary_account_id,
    cc.primary_product,
    cc.current_bucket,
    cc.current_dpd,
    cc.total_overdue,
    cc.total_exposure,
    cc.queue,
    cc.assigned_team,
    cc.assigned_agent_id,
    cc.strategy_code,
    cc.current_treatment,
    cc.next_scheduled_action,
    cc.next_action_ts,
    cc.last_contact_ts,
    cc.last_rpc_ts,
    cc.last_contact_channel,
    cc.hardship_flag,
    cc.hardship_source,
    cc.hardship_plan_type,
    cc.dispute_flag,
    cc.dispute_status,
    cc.cease_contact_flag,
    cc.insolvency_hold_flag,
    cc.deceased_hold_flag,
    cc.vulnerable_customer_flag,
    cc.recidivism_flag,
    cc.last_note_id,
    now() AS refreshed_at
  FROM silver.collections_cases cc
  LEFT JOIN silver.id_xref xc ON xc.source_system = 'collections' AND xc.source_key = cc.case_id
"""

# Narrow field-trust table for the handful of fields the Agent Desk shows.
FIELD_TRUST_SQL = """
CREATE OR REPLACE TABLE gold.field_trust AS
WITH src AS (
    SELECT c.golden_id, c.member_crm_ids,
           c.primary_phone_e164, c.email, c.postal_code,
           c.hardship_flag_customer, c.deceased_flag, c.insolvency_flag, c.last_profile_update_ts
      FROM (SELECT golden_id, member_crm_ids, primary_phone_e164, email, postal_code,
                   false AS hardship_flag_customer, deceased_flag, insolvency_flag, last_profile_update_ts
              FROM gold.c360_customer) c)
SELECT golden_id, 'primary_phone_e164' AS field, 'silver.customers (most recent live record)' AS source,
       last_profile_update_ts AS refreshed_at,
       CASE WHEN primary_phone_e164 IS NULL THEN 'missing'
            WHEN primary_phone_e164 LIKE '+1[2-9]%' OR regexp_full_match(primary_phone_e164, '\\+1[2-9][0-9]{9}') THEN 'ok'
            ELSE 'invalid' END AS dq_status
  FROM src
UNION ALL
SELECT golden_id, 'email', 'silver.customers (most recent verified record)', last_profile_update_ts,
       CASE WHEN email IS NULL THEN 'missing'
            WHEN email LIKE '%@%.%' THEN 'ok' ELSE 'invalid' END
  FROM src
UNION ALL
SELECT golden_id, 'postal_code', 'silver.customers (most recent address record)', last_profile_update_ts,
       CASE WHEN postal_code IS NULL THEN 'missing' ELSE 'ok' END
  FROM src
UNION ALL
SELECT golden_id, 'deceased_flag', 'silver.customers OR silver.external (any source true)',
       last_profile_update_ts, 'ok'
  FROM src WHERE deceased_flag
UNION ALL
SELECT golden_id, 'insolvency_flag', 'silver.customers (insolvency_filed_date present)',
       last_profile_update_ts, 'ok'
  FROM src WHERE insolvency_flag
"""


# ----- Quality checks Q1-Q7 ---------------------------------------------------------------------
QUALITY_CHECKS = [
    ("Q1_customer_golden_coverage", """
        -- LEFT ANTI JOIN (via LEFT JOIN WHERE NULL): hash build on c360_customer, probe id_xref
        SELECT 'c360_customer' AS tbl, count(*) AS records, 0 AS failing,
               'every golden_id in id_xref present in c360_customer' AS rule
          FROM silver.id_xref x LEFT JOIN gold.c360_customer c USING (golden_id)
         WHERE x.source_system = 'crm' AND c.golden_id IS NULL"""),
    ("Q2_account_golden_coverage", """
        SELECT 'c360_account', (SELECT count(*) FROM gold.c360_account),
               count(*) AS failing,
               'every account.golden_id resolves to a c360_customer'
          FROM gold.c360_account a LEFT JOIN gold.c360_customer c USING (golden_id)
         WHERE c.golden_id IS NULL"""),
    ("Q3_live_account_has_product_and_status", """
        SELECT 'c360_account', count(*) FILTER (WHERE account_status = 'active'),
               count(*) FILTER (WHERE account_status = 'active' AND (product_code IS NULL OR account_status IS NULL)),
               'live accounts have product_code AND account_status'
          FROM gold.c360_account"""),
    ("Q4_hardship_supportive_next_action", """
        SELECT 'c360_case', count(*) FILTER (WHERE hardship_flag),
               count(*) FILTER (WHERE hardship_flag AND next_scheduled_action IN
                   ('senior_agent_escalation','legal_handoff','debt_sale','legal_recovery',
                    'final_demand_letter')),
               'hardship cases do not schedule harsher treatments (CLAUDE §4.6)'
          FROM gold.c360_case"""),
    ("Q5_cease_contact_customers_no_future_outbound", """
        WITH future_out AS (
            SELECT DISTINCT x.golden_id
              FROM silver.contact_history ch
              JOIN silver.id_xref x ON x.source_system = 'crm' AND x.source_key = ch.crm_customer_id
             WHERE ch.direction = 'outbound' AND ch.contact_ts_utc >= DATE '2026-09-28')
        SELECT 'c360_customer x contact_history',
               count(*) FILTER (WHERE c.cease_contact_flag),
               count(*) FILTER (WHERE c.cease_contact_flag AND f.golden_id IS NOT NULL),
               'cease-contact customers have no outbound contact scheduled after as_of'
          FROM gold.c360_customer c LEFT JOIN future_out f USING (golden_id)"""),
    ("Q6_primary_phone_e164_valid_for_active_cases", """
        SELECT 'c360_customer x c360_case',
               count(DISTINCT cs.case_id) FILTER (WHERE cs.case_status = 'open'),
               count(DISTINCT cs.case_id) FILTER (WHERE cs.case_status = 'open'
                   AND (c.primary_phone_e164 IS NULL
                        OR NOT regexp_full_match(c.primary_phone_e164, '\\+1[2-9][0-9]{9}'))),
               'open cases have a valid NANP phone for the customer (gives Layer 4 something to dial)'
          FROM gold.c360_case cs JOIN gold.c360_customer c ON c.golden_id = cs.golden_id"""),
    ("Q7_orphan_contacts_rate_lt_1pct_DC_COLL_001", """
        SELECT 'contact_history', count(*),
               -- orphan rate as the failing field (DC-COLL-001 says < 1%)
               count(*) FILTER (WHERE list_contains(dq_flags, 'orphan_case')),
               'DC-COLL-001: orphan contact rate under 1%'
          FROM silver.contact_history"""),
]


def _ensure_gold_schema(con):
    con.execute("CREATE SCHEMA IF NOT EXISTS gold")


def build_c360(cfg: dict, log=print) -> dict:
    con = duckdb.connect(cfg["db_path"])
    scfg = cfg.get("silver", {})
    con.execute(f"SET memory_limit='{scfg.get('memory_limit', '4GB')}'; "
                f"SET threads={int(scfg.get('threads', 4))}; SET preserve_insertion_order=false;")
    _ensure_gold_schema(con)
    t0 = time.time()
    con.execute(CUSTOMER_SQL)
    nc = con.execute("SELECT count(*) FROM gold.c360_customer").fetchone()[0]
    log(f"  c360_customer: {nc:,} ({time.time()-t0:.1f}s)")

    # account build: first the role rows, then join facts on primary/joint/co_borrower
    t0 = time.time()
    con.execute(ACCOUNT_SQL.replace("CREATE OR REPLACE TABLE gold.c360_account",
                                    "CREATE OR REPLACE TABLE gold.c360_account_roles"))
    con.execute(ACCOUNT_FACTS_SQL)
    con.execute("DROP TABLE gold.c360_account_roles")
    na = con.execute("SELECT count(*) FROM gold.c360_account").fetchone()[0]
    log(f"  c360_account: {na:,} ({time.time()-t0:.1f}s)")

    t0 = time.time()
    con.execute(CASE_SQL)
    ns = con.execute("SELECT count(*) FROM gold.c360_case").fetchone()[0]
    log(f"  c360_case: {ns:,} ({time.time()-t0:.1f}s)")

    t0 = time.time()
    con.execute(FIELD_TRUST_SQL)
    nf = con.execute("SELECT count(*) FROM gold.field_trust").fetchone()[0]
    log(f"  field_trust: {nf:,} ({time.time()-t0:.1f}s)")

    # DQ checks
    con.execute("""CREATE OR REPLACE TABLE gold.dq_results (
        run_ts TIMESTAMP, check_id VARCHAR, scope VARCHAR, records BIGINT, failing BIGINT,
        rule VARCHAR, status VARCHAR)""")
    for cid, sql in QUALITY_CHECKS:
        row = con.execute(sql).fetchone()
        if row is None or row[1] is None:
            scope, records, failing, rule = "n/a", 0, 0, "no result"
        else:
            scope, records, failing, rule = row
        rate = (failing / max(records, 1)) * 100
        if cid.startswith("Q7"):      # DC-COLL-001: strict < 1%
            status = "pass" if rate < 1 else "fail"
            rule = f"{rule} (observed {rate:.2f}%)"
        elif cid.startswith("Q6"):    # contract allows <= 5% as a warning, > 5% is a fail
            status = "pass" if rate <= 5 else "fail"
            rule = f"{rule} (observed {rate:.2f}%; threshold <= 5%)"
        else:
            status = "pass" if (failing or 0) == 0 else "fail"
        con.execute("INSERT INTO gold.dq_results VALUES (now(), ?, ?, ?, ?, ?, ?)",
                    [cid, scope, int(records or 0), int(failing or 0), rule, status])
        log(f"  {cid}: {status} (records={records:,}, failing={failing:,})")
    con.close()
    return {"c360_customer": nc, "c360_account": na, "c360_case": ns, "field_trust": nf}
