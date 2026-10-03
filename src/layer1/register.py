"""Layer 1, step 0: register every source file as a DuckDB object.

Two schemas are created:
  raw.<table>  every column as VARCHAR. Exactly what the file says: keeps leading zeros,
               NA codes and mixed date formats so the cleaning step can see and log them.
  main.<table> typed version (DuckDB type detection) used for early exploration and Q&A
               until the silver/gold tables replace it.

Small CSV tables are materialised into the DuckDB file (fast repeated queries).
Parquet history tables stay as views over the files (no copy, ~40M rows).
Folders listed in config `hidden_dirs` (labels, gold answers) are registered under the
`hidden` schema and are never exposed to Layer 2.
"""
from __future__ import annotations
import re, time
from collections import defaultdict
from pathlib import Path
import duckdb

TABLES = [
    "customers", "card_accounts", "loan_accounts", "deposit_accounts", "collections_cases",
    "contact_history", "promises_to_pay", "agent_notes", "call_transcripts", "voice_samples",
    "external", "loan_instalments", "transactions", "card_statements", "account_monthly_snapshot",
    "bureau_history", "salary_credit_history", "model_scores", "offers", "metric_definitions",
    "benchmark_questions", "reference_documents", "hardship_programs", "qa_checklist", "agents",
    "case_assignment_history", "agent_shifts", "channel_capacity", "ops_events", "geo_reference",
    "code_lookups",
]
EXTS = {".csv", ".parquet", ".json", ".jsonl"}
YEAR_SUFFIX = re.compile(r"[_\-]?(19|20)\d{2}$")


def _table_for(path: Path, root: Path) -> str | None:
    stem = YEAR_SUFFIX.sub("", path.stem.lower())
    if stem in TABLES:
        return stem
    for parent in path.relative_to(root).parents:
        name = YEAR_SUFFIX.sub("", parent.name.lower().replace("year=", ""))
        if name in TABLES:
            return name
    return None


def discover(data_dir: str, hidden_dirs: list[str]) -> tuple[dict, dict]:
    """Return ({table: [files]}, {hidden_name: [files]})."""
    root = Path(data_dir)
    if not root.exists():
        raise FileNotFoundError(f"data_dir not found: {root}. Edit config.yaml.")
    found, hidden = defaultdict(list), defaultdict(list)
    for p in sorted(root.rglob("*")):
        if p.suffix.lower() not in EXTS or not p.is_file():
            continue
        rel_parts = {x.lower() for x in p.relative_to(root).parts[:-1]}
        if rel_parts & {h.lower() for h in hidden_dirs}:
            hidden[p.stem.lower()].append(p)
            continue
        t = _table_for(p, root)
        if t:
            found[t].append(p)
    return found, hidden


def _files_sql(files: list[Path]) -> str:
    return "[" + ", ".join("'" + str(f).replace("'", "''") + "'" for f in files) + "]"


def _source_expr(files: list[Path], varchar: bool) -> str:
    exts = {f.suffix.lower() for f in files}
    lst = _files_sql(files)
    if exts == {".parquet"}:
        return f"read_parquet({lst}, union_by_name=true, filename=true)"
    if exts <= {".json", ".jsonl"}:
        return f"read_json_auto({lst}, union_by_name=true, maximum_object_size=104857600)"
    csv_files = [f for f in files if f.suffix.lower() == ".csv"]
    lst = _files_sql(csv_files)
    opts = "header=true, union_by_name=true, sample_size=200000"
    if varchar:
        opts += ", all_varchar=true"
    return f"read_csv({lst}, {opts})"


def register_all(cfg: dict, materialise: bool = True, log=print) -> duckdb.DuckDBPyConnection:
    found, hidden = discover(cfg["data_dir"], cfg.get("hidden_dirs", []))
    con = duckdb.connect(cfg["db_path"])
    con.execute("CREATE SCHEMA IF NOT EXISTS raw; CREATE SCHEMA IF NOT EXISTS hidden;")
    missing = [t for t in TABLES if t not in found]
    for t, files in found.items():
        # a table with CSV/Parquet metadata ignores sidecar JSON (e.g. transcript bodies)
        tabular = [f for f in files if f.suffix.lower() in {".csv", ".parquet"}]
        files = tabular or files
        t0 = time.time()
        is_parquet = all(f.suffix.lower() == ".parquet" for f in files)
        raw_src = _source_expr(files, varchar=True)
        con.execute(f"CREATE OR REPLACE VIEW raw.{t} AS SELECT * FROM {raw_src}")
        typed_src = _source_expr(files, varchar=False)
        kind = "VIEW" if (is_parquet or not materialise) else "TABLE"
        try:
            con.execute(f"CREATE OR REPLACE {kind} main.{t} AS SELECT * FROM {typed_src}")
        except duckdb.Error as e:  # type detection failed on messy data: fall back to text
            log(f"  ! typed load failed for {t} ({str(e)[:120]}); using VARCHAR copy")
            con.execute(f"CREATE OR REPLACE {kind} main.{t} AS SELECT * FROM {raw_src}")
        n = con.execute(f"SELECT count(*) FROM main.{t}").fetchone()[0]
        log(f"  {t:<28} {kind:<5} {len(files):>3} file(s) {n:>12,} rows  {time.time()-t0:5.1f}s")
    for name, files in hidden.items():
        if all(f.suffix.lower() == ".csv" for f in files):
            safe = re.sub(r"\W", "_", name)
            con.execute(f"CREATE OR REPLACE VIEW hidden.{safe} AS SELECT * FROM {_source_expr(files, True)}")
    if missing:
        log(f"  not found (check names/paths): {', '.join(missing)}")
    log(f"  hidden (never shown to Layer 2): {', '.join(sorted(hidden)) or 'none'}")
    return con
