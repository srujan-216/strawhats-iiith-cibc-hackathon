"""Customer-level sampling shared by every pipeline step (`--sample N`, fixed seed 42).

A sample is N CRM customers, picked by a seeded md5 order (same N + seed -> same customers on
every machine and every run, and a larger N is a superset of a smaller one). Everything that
belongs to those customers follows them, using only links the source data already carries:

  sample_crm       N CRM records + any CRM records that point to them via duplicate_of_crm_id
  sample_accounts  account ids those customers hold (account_monthly_snapshot, salary_credit_history)
  sample_cases     collections cases opened for those customers (coll_customer_ref)
  sample_src_refs  (system, src_customer_ref) of the card/loan/deposit systems for those accounts,
                   plus the 10-digit CIF (left-padded) used by external / bureau_history

These are TEMP tables, so they also work on a read-only connection. Use `sample_filter()` to get the
WHERE predicate for any table.
"""
from __future__ import annotations
import time

SEED = 42

# table -> (key column, sample table, sample column); a table not listed is not customer-level
_KEYS = {
    "customers": ("crm_customer_id", "sample_crm", "crm_customer_id"),
    "contact_history": ("crm_customer_id", "sample_crm", "crm_customer_id"),
    "promises_to_pay": ("crm_customer_id", "sample_crm", "crm_customer_id"),
    "agent_notes": ("crm_customer_id", "sample_crm", "crm_customer_id"),
    "call_transcripts": ("crm_customer_id", "sample_crm", "crm_customer_id"),
    "model_scores": ("crm_customer_id", "sample_crm", "crm_customer_id"),
    "account_monthly_snapshot": ("crm_customer_id", "sample_crm", "crm_customer_id"),
    "salary_credit_history": ("crm_customer_id", "sample_crm", "crm_customer_id"),
    "collections_cases": ("case_id", "sample_cases", "case_id"),
    "case_assignment_history": ("case_id", "sample_cases", "case_id"),
    "offers": ("case_id", "sample_cases", "case_id"),
    "card_accounts": ("card_account_id", "sample_accounts", "account_id"),
    "card_statements": ("card_account_id", "sample_accounts", "account_id"),
    "loan_accounts": ("loan_id", "sample_accounts", "account_id"),
    "loan_instalments": ("loan_id", "sample_accounts", "account_id"),
    "deposit_accounts": ("deposit_account_id", "sample_accounts", "account_id"),
    "transactions": ("account_id", "sample_accounts", "account_id"),
    "external": ("bank_subject_ref", "sample_cif", "cif"),
    "bureau_history": ("bank_subject_ref", "sample_cif", "cif"),
}


def build_sample(con, n: int, seed: int = SEED, schema: str = "main", log=print) -> dict:
    """Create the sample_* TEMP tables for N customers. Returns row counts per sample table."""
    t0 = time.time()
    s = schema
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE sample_crm AS
        WITH picked AS (
            SELECT crm_customer_id FROM {s}.customers
            WHERE duplicate_of_crm_id IS NULL OR duplicate_of_crm_id = ''
            ORDER BY md5('{int(seed)}:' || crm_customer_id) LIMIT {int(n)})
        SELECT crm_customer_id FROM picked
        UNION
        SELECT c.crm_customer_id FROM {s}.customers c JOIN picked p ON c.duplicate_of_crm_id = p.crm_customer_id""")
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE sample_accounts AS
        SELECT DISTINCT account_id FROM {s}.account_monthly_snapshot
        WHERE crm_customer_id IN (SELECT crm_customer_id FROM sample_crm)
        UNION
        SELECT DISTINCT deposit_account_id FROM {s}.salary_credit_history
        WHERE crm_customer_id IN (SELECT crm_customer_id FROM sample_crm)""")
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE sample_cases AS
        SELECT case_id FROM {s}.collections_cases
        WHERE coll_customer_ref IN (SELECT crm_customer_id FROM sample_crm)""")
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE sample_src_refs AS
        SELECT DISTINCT 'cards' AS system, src_customer_ref FROM {s}.card_accounts
          WHERE card_account_id IN (SELECT account_id FROM sample_accounts)
        UNION SELECT DISTINCT 'loans', src_customer_ref FROM {s}.loan_accounts
          WHERE loan_id IN (SELECT account_id FROM sample_accounts)
        UNION SELECT DISTINCT 'deposits', src_customer_ref FROM {s}.deposit_accounts
          WHERE deposit_account_id IN (SELECT account_id FROM sample_accounts)""")
    # the core-banking CIF is 10 digits but some deposit rows lost their leading zeros
    con.execute("""
        CREATE OR REPLACE TEMP TABLE sample_cif AS
        SELECT DISTINCT lpad(src_customer_ref, 10, '0') AS cif FROM sample_src_refs
        WHERE system = 'deposits' AND regexp_full_match(src_customer_ref, '[0-9]+')""")
    counts = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
              for t in ("sample_crm", "sample_accounts", "sample_cases", "sample_src_refs", "sample_cif")}
    log(f"  sample N={n} seed={seed}: " + ", ".join(f"{k}={v:,}" for k, v in counts.items())
        + f"  ({time.time() - t0:.1f}s)")
    return counts


def sample_filter(table: str, alias: str | None = None, n: int | None = None) -> str:
    """SQL predicate restricting `table` to the sample (call build_sample first).

    Returns 'TRUE' when n is None (full data) or the table is not customer-level, so callers can
    always write `WHERE {sample_filter(...)}`.
    """
    if n is None or table not in _KEYS:
        return "TRUE"
    col, st, sc = _KEYS[table]
    ref = f"{alias}.{col}" if alias else col
    if st == "sample_cif":
        ref = f"lpad({ref}, 10, '0')"
    return f"{ref} IN (SELECT {sc} FROM {st})"
