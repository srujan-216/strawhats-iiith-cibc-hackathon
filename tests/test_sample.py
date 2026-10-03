import duckdb
from src.common.sample import build_sample, sample_filter


def _toy():
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE customers AS SELECT * FROM (VALUES
            ('A-1', NULL), ('A-2', NULL), ('A-3', NULL), ('A-4', NULL), ('A-5', NULL), ('A-9', 'A-1'))
            t(crm_customer_id, duplicate_of_crm_id);
        CREATE TABLE account_monthly_snapshot AS SELECT * FROM (VALUES
            ('C-1', 'A-1'), ('L-2', 'A-2'), ('C-3', 'A-3'), ('CHQ-4', 'A-4')) t(account_id, crm_customer_id);
        CREATE TABLE salary_credit_history AS SELECT * FROM (VALUES ('CHQ-1', 'A-1')) t(deposit_account_id, crm_customer_id);
        CREATE TABLE collections_cases AS SELECT * FROM (VALUES ('CS-1', 'A-1'), ('CS-2', 'A-5')) t(case_id, coll_customer_ref);
        CREATE TABLE card_accounts AS SELECT * FROM (VALUES ('C-1', 'CX1'), ('C-3', 'CX3')) t(card_account_id, src_customer_ref);
        CREATE TABLE loan_accounts AS SELECT * FROM (VALUES ('L-2', 'B2')) t(loan_id, src_customer_ref);
        CREATE TABLE deposit_accounts AS SELECT * FROM (VALUES ('CHQ-1', '1234567'), ('CHQ-4', '0000000004')) t(deposit_account_id, src_customer_ref);
    """)
    return con


def test_sample_is_deterministic_and_nested():
    con = _toy()
    build_sample(con, 2, log=lambda *_: None)
    first = sorted(r[0] for r in con.execute("SELECT * FROM sample_crm").fetchall())
    build_sample(con, 2, log=lambda *_: None)
    assert first == sorted(r[0] for r in con.execute("SELECT * FROM sample_crm").fetchall())
    build_sample(con, 4, log=lambda *_: None)
    bigger = {r[0] for r in con.execute("SELECT * FROM sample_crm").fetchall()}
    assert set(first) <= bigger


def test_sample_follows_duplicates_accounts_and_cif():
    con = _toy()
    counts = build_sample(con, 5, log=lambda *_: None)
    assert counts["sample_crm"] == 6                       # 5 picked + duplicate A-9 of A-1
    cif = {r[0] for r in con.execute("SELECT cif FROM sample_cif").fetchall()}
    assert "0001234567" in cif                              # leading zeros restored
    rows = con.execute(f"SELECT count(*) FROM collections_cases WHERE {sample_filter('collections_cases', n=5)}").fetchone()[0]
    assert rows == 2


def test_filter_is_true_without_sample():
    assert sample_filter("customers", n=None) == "TRUE"
    assert sample_filter("metric_definitions", n=10) == "TRUE"
    assert "lpad(e.bank_subject_ref" in sample_filter("external", "e", n=10)
