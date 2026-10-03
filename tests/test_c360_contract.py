"""The YAML contract must match gold.c360_customer's real columns (names + types)."""
from pathlib import Path
import duckdb
import pytest
import yaml

CONTRACT = Path("contracts/c360_customer.yaml")


def _types():
    con = duckdb.connect("warehouse/maple.duckdb", read_only=True)
    try:
        return dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                                "WHERE table_schema='gold' AND table_name='c360_customer'").fetchall())
    finally:
        con.close()


@pytest.mark.skipif(not CONTRACT.exists(), reason="contract missing")
@pytest.mark.skipif(not Path("warehouse/maple.duckdb").exists(), reason="warehouse missing (run `python run.py c360`)")
def test_contract_matches_gold_c360_customer_columns():
    types = _types()
    if not types:
        pytest.skip("gold.c360_customer not built yet")
    schema = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))["schema"]
    declared = {c["name"]: c["type"] for c in schema}

    missing_in_table = sorted(set(declared) - set(types))
    missing_in_contract = sorted(set(types) - set(declared))
    assert not missing_in_table, f"contract declares columns not in gold.c360_customer: {missing_in_table}"
    assert not missing_in_contract, f"gold.c360_customer has columns not in contract: {missing_in_contract}"

    def _norm(t):
        # drop size spec and the "WITH TIME ZONE" tail (now() returns TIMESTAMPTZ)
        return t.upper().split("(")[0].replace("TIMESTAMP WITH TIME ZONE", "TIMESTAMP").strip()
    for c, want in declared.items():
        got = types[c]
        if _norm(want) == "VARCHAR[]":
            assert got.startswith("VARCHAR["), f"{c}: contract says {want}, got {got}"
        else:
            assert _norm(want) == _norm(got), f"{c}: contract says {want}, got {got}"
