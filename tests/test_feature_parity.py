"""Offline (gold.features_offline, decision_date=SNAPSHOT_DATE) must match online for every
feature on a random 1,000-key sample. If they differ, the "point-in-time at today" shortcut
has drifted from the "latest state" refresh and Layer 4 will train on different numbers from
what it scores on."""
import duckdb
import pytest
from pathlib import Path
from src.layer3.features import NUMERIC_COLUMNS, SNAPSHOT_DATE

DB = Path("warehouse/maple.duckdb")


@pytest.mark.skipif(not DB.exists(), reason="warehouse missing")
def test_offline_equals_online_on_1000_keys():
    con = duckdb.connect(str(DB), read_only=True)
    try:
        tabs = {r[0] for r in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='gold'").fetchall()}
        if not {"features_offline", "features_online"} <= tabs:
            pytest.skip("features_* tables not built")
        keys = con.execute("""SELECT golden_id FROM gold.features_online USING SAMPLE 1000 ROWS
                              (RESERVOIR, 42)""").fetchall()
        ids = [k[0] for k in keys]
        assert len(ids) == 1000
        placeholders = ",".join("?" for _ in ids)
        cols = ", ".join(NUMERIC_COLUMNS)
        off = con.execute(f"SELECT golden_id, {cols} FROM gold.features_offline "
                          f"WHERE decision_date = DATE '{SNAPSHOT_DATE}' AND golden_id IN ({placeholders}) "
                          f"ORDER BY golden_id", ids).fetchall()
        on = con.execute(f"SELECT golden_id, {cols} FROM gold.features_online "
                         f"WHERE golden_id IN ({placeholders}) ORDER BY golden_id", ids).fetchall()
        assert len(off) == len(on) == 1000
        for o, n in zip(off, on):
            # exact equality for ints/bools; equal within 1e-9 for doubles
            assert o[0] == n[0]
            for i, col in enumerate(NUMERIC_COLUMNS, start=1):
                a, b = o[i], n[i]
                if a is None and b is None: continue
                if isinstance(a, float) or isinstance(b, float):
                    assert a is not None and b is not None, f"{col}: {a} vs {b}"
                    assert abs(a - b) < 1e-9, f"{col}: {a} vs {b} on {o[0]}"
                else:
                    assert a == b, f"{col}: {a} vs {b} on {o[0]}"
    finally:
        con.close()
