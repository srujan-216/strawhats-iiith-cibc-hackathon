"""Identity resolution: CRM clustering, golden_id choice, deterministic bridges."""
import duckdb
import pytest
from src.layer1.match import build_crm_clusters, build_deterministic_links, build_id_xref


def _tables(con):
    """Minimal silver.* and main.* tables used by match.py's SQL."""
    con.execute("CREATE SCHEMA silver; CREATE SCHEMA IF NOT EXISTS main")
    con.execute("""CREATE TABLE silver.customers (crm_customer_id VARCHAR, duplicate_of_crm_id VARCHAR,
        national_id_hash VARCHAR, cdc_operation VARCHAR)""")
    con.execute("""CREATE TABLE silver.card_accounts (card_account_id VARCHAR, src_customer_ref VARCHAR)""")
    con.execute("""CREATE TABLE silver.loan_accounts (loan_id VARCHAR, src_customer_ref VARCHAR)""")
    con.execute("""CREATE TABLE silver.deposit_accounts (deposit_account_id VARCHAR, src_customer_ref VARCHAR)""")
    con.execute("""CREATE TABLE silver.collections_cases (case_id VARCHAR, coll_customer_ref VARCHAR)""")
    con.execute("""CREATE TABLE silver.external (bureau_request_id VARCHAR, bank_subject_ref VARCHAR)""")
    con.execute("""CREATE TABLE main.account_monthly_snapshot (product_type VARCHAR, account_id VARCHAR,
        crm_customer_id VARCHAR)""")


def test_crm_cluster_uses_pointer_and_national_id_hash():
    con = duckdb.connect(); _tables(con)
    # cluster 1: pointer A-9 -> A-1; shared hash across A-1/A-2
    # cluster 2: shared hash C-1/C-2
    # D-1 alone
    con.execute("""INSERT INTO silver.customers VALUES
        ('A-1', NULL, 'h1', 'U'), ('A-2', NULL, 'h1', 'U'), ('A-9', 'A-1', NULL, 'U'),
        ('C-1', NULL, 'h2', 'U'), ('C-2', NULL, 'h2', 'U'),
        ('D-1', NULL, NULL, 'U')""")
    big = build_crm_clusters(con, sample_n=None, log=lambda *_: None)
    assert big == 2
    rows = {r[0]: r[1] for r in con.execute("SELECT crm_customer_id, cluster_id FROM crm_clusters").fetchall()}
    assert rows["A-1"] == rows["A-2"] == rows["A-9"] == "A-1"
    assert rows["C-1"] == rows["C-2"] == "C-1"
    assert rows["D-1"] == "D-1"


def test_golden_id_prefers_live_over_deleted():
    """A deleted record cannot be the canonical cluster_id, so historical links still resolve to a live id.
    If every member is deleted, fall back to the overall min."""
    con = duckdb.connect(); _tables(con)
    # A-1 deleted, A-2 live, shared hash -> cluster_id must be A-2, not A-1
    con.execute("""INSERT INTO silver.customers VALUES
        ('A-1', NULL, 'h1', 'D'), ('A-2', NULL, 'h1', 'U'),
        ('Z-1', NULL, 'h2', 'D'), ('Z-2', NULL, 'h2', 'D')""")   # all deleted -> min of all
    build_crm_clusters(con, sample_n=None, log=lambda *_: None)
    rows = {r[0]: (r[1], r[2]) for r in con.execute(
        "SELECT crm_customer_id, cluster_id, is_deleted FROM crm_clusters").fetchall()}
    assert rows["A-1"] == ("A-2", True) and rows["A-2"] == ("A-2", False)
    # deleted-only cluster: canonical is the min id (both are deleted)
    assert rows["Z-1"] == ("Z-1", True) and rows["Z-2"] == ("Z-1", True)


def test_deterministic_bridges_link_sources_to_crm():
    con = duckdb.connect(); _tables(con)
    con.execute("""INSERT INTO silver.customers VALUES ('A-1', NULL, NULL, 'U'), ('B-1', NULL, NULL, 'U');
        INSERT INTO silver.card_accounts VALUES ('C-100', 'CX1');
        INSERT INTO silver.loan_accounts VALUES ('L-200', 'B1');
        INSERT INTO silver.deposit_accounts VALUES ('CHQ-1', '0000000001');
        INSERT INTO silver.collections_cases VALUES ('CS-1', 'A-1');
        INSERT INTO silver.external VALUES ('EQ-1', '0000000001');
        INSERT INTO main.account_monthly_snapshot VALUES
            ('card', 'C-100', 'A-1'),
            ('personal_loan', 'L-200', 'B-1'),
            ('chequing', 'CHQ-1', 'A-1')""")
    build_crm_clusters(con, sample_n=None, log=lambda *_: None)
    build_deterministic_links(con, sample_n=None, log=lambda *_: None)
    rows = {(r[0], r[1]): (r[2], r[3]) for r in con.execute(
        "SELECT source_system, source_key, crm_customer_id, match_method FROM det_links").fetchall()}
    assert rows[("cards", "C-100")] == ("A-1", "bridge_ams")
    assert rows[("loans", "L-200")] == ("B-1", "bridge_ams")
    assert rows[("deposits", "CHQ-1")] == ("A-1", "bridge_ams")
    assert rows[("collections", "CS-1")] == ("A-1", "bridge_coll")
    assert rows[("external", "EQ-1")] == ("A-1", "bridge_cif")
    # id_xref: all deterministic rows land here with confidence 1.0 and the right golden_id
    con.execute("CREATE OR REPLACE TEMP TABLE _prob_pairs AS SELECT NULL::VARCHAR crm_a, NULL::VARCHAR crm_b, NULL::DOUBLE p, NULL::VARCHAR band WHERE false")
    build_id_xref(con, [], log=lambda *_: None)
    out = {(r[0], r[1]): (r[2], r[3], r[4]) for r in con.execute(
        "SELECT source_system, source_key, golden_id, match_method, match_confidence FROM silver.id_xref").fetchall()}
    assert out[("cards", "C-100")] == ("A-1", "bridge_ams", 1.0)
    assert out[("crm", "A-1")] == ("A-1", "crm_identity", 1.0)


def test_golden_id_stable_across_runs():
    """Running the same input twice yields the same golden_id for every record (deterministic)."""
    def run():
        con = duckdb.connect(); _tables(con)
        con.execute("INSERT INTO silver.customers VALUES ('A-1', NULL, 'h1', 'D'), ('A-2', NULL, 'h1', 'U'), "
                    "('A-3', 'A-1', NULL, 'U'), ('X-1', NULL, NULL, 'U')")
        build_crm_clusters(con, sample_n=None, log=lambda *_: None)
        return sorted(con.execute("SELECT crm_customer_id, cluster_id FROM crm_clusters").fetchall())
    assert run() == run()
