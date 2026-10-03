"""SQL guard: the only way Layer 2 can touch data.

Controls (independent, all must pass):
 1. parse with sqlglot (DuckDB dialect); exactly one statement
 2. statement is a read-only query (SELECT / UNION / WITH ... SELECT); no DDL, DML or commands
 3. every table referenced is on the allowlist (main schema, Layer-2-visible tables) or a CTE
 4. no file-reading or system table functions (read_csv, read_parquet, glob, ...)
 5. a row LIMIT is added if missing; execution has a timeout (see execute_guarded)
Plus, at connection level: the database is opened read_only=True.
"""
from __future__ import annotations
import threading
import sqlglot
from sqlglot import exp


class GuardError(Exception):
    pass


_FORBIDDEN_NODES = tuple(t for t in (
    getattr(exp, n, None) for n in (
        "Insert", "Update", "Delete", "Drop", "Create", "Alter", "AlterTable", "Command",
        "Merge", "TruncateTable", "Copy", "Set", "Pragma", "Use", "Grant", "Revoke",
        "Attach", "Detach", "Install", "LoadData", "Transaction", "Commit", "Rollback"))
    if t is not None)

_BLOCKED_FUNCS = {
    "read_csv", "read_csv_auto", "read_parquet", "parquet_scan", "read_json", "read_json_auto",
    "read_ndjson", "read_text", "read_blob", "glob", "sniff_csv", "query", "query_table",
    "duckdb_settings", "duckdb_secrets", "pragma_table_info", "getenv", "read_xlsx", "st_read",
}


def _func_name(node: exp.Expression) -> str:
    if isinstance(node, exp.Anonymous):
        return str(node.this).lower()
    return (node.sql_name() if hasattr(node, "sql_name") else node.key).lower()


def validate(sql: str, allowed_tables: set[str], row_limit: int = 1000,
             blocked_columns: set[str] | None = None) -> str:
    sql = sql.strip().rstrip(";").strip()
    if not sql:
        raise GuardError("empty query")
    try:
        statements = sqlglot.parse(sql, read="duckdb")
    except sqlglot.errors.ParseError as e:
        raise GuardError(f"could not parse SQL: {str(e)[:200]}")
    statements = [s for s in statements if s is not None]
    if len(statements) != 1:
        raise GuardError("exactly one statement is allowed")
    tree = statements[0]
    if not isinstance(tree, (exp.Select, exp.Union, exp.Intersect, exp.Except, exp.Subquery)):
        raise GuardError(f"only SELECT queries are allowed (got {tree.key.upper()})")
    for node in tree.walk():
        if isinstance(node, _FORBIDDEN_NODES):
            raise GuardError(f"forbidden operation: {node.key.upper()}")
        if isinstance(node, exp.Func) and _func_name(node) in _BLOCKED_FUNCS:
            raise GuardError(f"function not allowed: {_func_name(node)}")
    blocked = {c.lower() for c in (blocked_columns or set())}
    for col in tree.find_all(exp.Column):
        if col.name.lower() in blocked:
            raise GuardError(f"protected attribute not allowed: {col.name}")
    cte_names = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    allowed = {t.lower() for t in allowed_tables}
    for t in tree.find_all(exp.Table):
        name = t.name.lower()
        schema = (t.db or "").lower()
        if not name:  # table function such as unnest(...) / range(...)
            continue
        if name in cte_names and not schema:
            continue
        if schema not in ("", "main") or t.catalog:
            raise GuardError(f"schema not allowed: {schema or t.catalog}.{name}")
        if name not in allowed:
            raise GuardError(f"table not allowed: {name}")
    if isinstance(tree, exp.Select) and not tree.args.get("limit"):
        tree = tree.limit(row_limit)
    elif not isinstance(tree, exp.Select):
        tree = exp.select("*").from_(tree.subquery("q")).limit(row_limit)
    return tree.sql(dialect="duckdb")


def execute_guarded(con, sql: str, timeout_s: int = 30):
    """Run an already-validated query with a hard timeout. Returns a pandas DataFrame."""
    result, error = {}, {}

    def _run():
        try:
            result["df"] = con.execute(sql).df()
        except Exception as e:  # noqa: BLE001 - surfaced to caller
            error["e"] = e

    th = threading.Thread(target=_run, daemon=True)
    th.start()
    th.join(timeout_s)
    if th.is_alive():
        con.interrupt()
        th.join(5)
        raise GuardError(f"query timed out after {timeout_s}s")
    if "e" in error:
        raise error["e"]
    return result["df"]
