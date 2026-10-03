"""Quick profile of every registered table -> reports/profile.md.

Per column: type, null %, approx distinct, min, max. This is the first input to the
data quality report (counts of issues per table)."""
from __future__ import annotations
from pathlib import Path
import duckdb


def profile(con: duckdb.DuckDBPyConnection, out_path: str, sample_rows: int | None = None) -> str:
    tables = [r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main' ORDER BY 1").fetchall()]
    lines = ["# Source profile", "", "| table | rows | columns |", "|---|---:|---:|"]
    details = []
    for t in tables:
        n = con.execute(f"SELECT count(*) FROM main.{t}").fetchone()[0]
        cols = con.execute(f"SELECT count(*) FROM information_schema.columns WHERE table_schema='main' AND table_name='{t}'").fetchone()[0]
        lines.append(f"| {t} | {n:,} | {cols} |")
        src = f"(SELECT * FROM main.{t} USING SAMPLE {sample_rows} ROWS)" if sample_rows else f"main.{t}"
        try:
            s = con.execute(f"SUMMARIZE {src}").df()
        except duckdb.Error as e:
            details += [f"\n## {t}\n", f"summarize failed: {e}"]
            continue
        s = s[["column_name", "column_type", "null_percentage", "approx_unique", "min", "max"]]
        s["min"] = s["min"].astype(str).str.slice(0, 30)
        s["max"] = s["max"].astype(str).str.slice(0, 30)
        details += [f"\n## {t} ({n:,} rows)\n", s.to_markdown(index=False)]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(lines + details), encoding="utf-8")
    return out_path
