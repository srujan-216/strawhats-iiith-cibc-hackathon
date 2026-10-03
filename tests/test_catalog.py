"""Catalog schema_block keeps the plan prompt small and still mentions the columns needed."""
import duckdb
from unittest.mock import patch
import pandas as pd
from src.layer2.catalog import Catalog


def _toy_catalog():
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE main.collections_cases (case_id VARCHAR, case_status VARCHAR, current_dpd BIGINT,
            current_bucket VARCHAR, assigned_agent_id VARCHAR, outcome VARCHAR, snapshot_date DATE,
            notes VARCHAR, extra_field VARCHAR, another_field VARCHAR);
        CREATE TABLE main.metric_definitions (metric_id VARCHAR, metric_name VARCHAR,
            business_definition VARCHAR, formula VARCHAR, grain VARCHAR, time_basis VARCHAR,
            default_filters VARCHAR, unit VARCHAR, synonyms VARCHAR, source_tables VARCHAR,
            certified_flag BOOLEAN);
    """)
    with patch.object(Catalog, "_load_dictionary", lambda self, d: None):
        cat = Catalog(con, "/no/such/dir")
    cat.col_desc = {("collections_cases", "case_status"): "open/closed status of the case"}
    cat.table_desc = {"collections_cases": "Collection cases."}
    return cat


def test_schema_block_shrinks_and_keeps_relevant_columns():
    cat = _toy_catalog()
    block = cat.schema_block(["collections_cases"], "How many open collections cases are there?")
    assert "case_status" in block                # relevant to the question
    assert "case_id" in block and "snapshot_date" in block   # structural (id / date)
    # extra_field/another_field are not relevant: they can be dropped once max_cols is hit
    assert len(block) < 2000                     # kept small
    assert "DESCRIPTION" not in block.upper() or len(block.split("\n")[1]) < 160


def test_default_table_fanout_dropped_to_three():
    cat = _toy_catalog()
    # tables default argument k=3 is the real check; make sure default call does not pick 5
    assert Catalog.relevant_tables.__defaults__[0] == 3
