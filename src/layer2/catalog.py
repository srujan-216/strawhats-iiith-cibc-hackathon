"""What Layer 2 is allowed to know: visible tables, their columns with descriptions,
certified metrics, and which columns are protected (never queryable)."""
from __future__ import annotations
import re
from pathlib import Path
import duckdb
import pandas as pd
from src.layer1.register import TABLES

# Tables Layer 2 must not read: benchmark metadata contains refusal flags and rubrics.
NOT_FOR_QA = {"benchmark_questions"}
# Protected attributes from the dictionary + proxies we exclude (see design doc 2.9).
EXTRA_BLOCKED = {"age", "age_band", "cpp_oas_deposit_flag", "customer_pitch_mean_hz",
                 "customer_pitch_std_hz", "fsa_income_index", "majority_language"}
_WORD = re.compile(r"[a-z0-9]+")


def _tokens(s: str) -> set[str]:
    out = set()
    for w in _WORD.findall(str(s).lower()):
        out.add(w)
        if w.endswith("s") and len(w) > 3:
            out.add(w[:-1])
    return out


class Catalog:
    def __init__(self, con: duckdb.DuckDBPyConnection, data_dir: str):
        present = {r[0] for r in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()}
        self.tables = sorted((present & set(TABLES)) - NOT_FOR_QA)
        cols = con.execute("SELECT table_name, column_name, data_type FROM information_schema.columns "
                           "WHERE table_schema='main' ORDER BY table_name, ordinal_position").fetchall()
        self.columns: dict[str, list[tuple[str, str]]] = {}
        for t, c, ty in cols:
            if t in self.tables:
                self.columns.setdefault(t, []).append((c, ty))
        self.col_desc, self.table_desc, self.protected = {}, {}, set(EXTRA_BLOCKED)
        self._load_dictionary(data_dir)
        self.metrics = (con.execute("SELECT * FROM main.metric_definitions").df()
                        if "metric_definitions" in present else pd.DataFrame())

    def _load_dictionary(self, data_dir: str):
        hits = list(Path(data_dir).rglob("DATA_DICTIONARY.xlsx")) + list(Path(data_dir).rglob("*ictionary*.xlsx"))
        if not hits:
            return
        x = pd.read_excel(hits[0], sheet_name=None)
        cols = x.get("Columns")
        if cols is not None:
            for _, r in cols.iterrows():
                self.col_desc[(str(r.get("Table")), str(r.get("Column")))] = str(r.get("Description", ""))[:110]
                if str(r.get("Sensitivity", "")).strip().lower() == "protected attribute":
                    self.protected.add(str(r.get("Column")).lower())
        tabs = x.get("Tables")
        if tabs is not None:
            for _, r in tabs.iterrows():
                self.table_desc[str(r.get("Table"))] = f"{r.get('Description', '')} One row per {r.get('One row per', '')}."

    # ---------- retrieval of relevant schema ----------
    def metric_matches(self, question: str, k: int = 3) -> pd.DataFrame:
        if self.metrics.empty:
            return self.metrics
        q = question.lower()
        qt = _tokens(question)

        def score(r):
            syns = [s.strip(" '\"") for s in re.split(r"[;|,\[\]]", str(r.get("synonyms", ""))) if s.strip(" '\"")]
            s = 3.0 * sum(1 for p in syns + [str(r.get("metric_name", ""))] if p and p.lower() in q)
            s += 0.3 * len(qt & _tokens(f"{r.get('metric_name','')} {r.get('business_definition','')}"))
            return s
        m = self.metrics.assign(_s=self.metrics.apply(score, axis=1))
        return m[m._s > 0.9].sort_values("_s", ascending=False).head(k)

    def relevant_tables(self, question: str, metric_rows: pd.DataFrame, k: int = 5) -> list[str]:
        qt = _tokens(question)
        scores = {}
        for t in self.tables:
            text = t.replace("_", " ") + " " + self.table_desc.get(t, "") + " " + " ".join(
                c.replace("_", " ") for c, _ in self.columns.get(t, []))
            scores[t] = 2.0 * len(qt & _tokens(t.replace("_", " "))) + 0.4 * len(qt & _tokens(text))
        picked = [t for t, s in sorted(scores.items(), key=lambda kv: -kv[1]) if s > 0][:k]
        for _, r in metric_rows.iterrows():
            for t in re.findall(r"[a-z_]+", str(r.get("source_tables", "")).lower()):
                if t in self.tables and t not in picked:
                    picked.append(t)
        return picked or ["collections_cases", "customers"]

    def schema_block(self, tables: list[str], question: str, max_cols: int = 60) -> str:
        qt = _tokens(question)
        out = []
        for t in tables:
            cols = [(c, ty) for c, ty in self.columns.get(t, []) if c.lower() not in self.protected]
            def rank(ct):
                c = ct[0].lower()
                key = c.endswith(("_id", "_ref", "_date", "_ts")) or c in {"status", "segment", "province_code"}
                return -(3 * key + len(qt & _tokens(c.replace("_", " ") + " " + self.col_desc.get((t, ct[0]), ""))))
            cols = sorted(cols, key=rank)[:max_cols]
            lines = [f"- {c} ({ty}): {self.col_desc.get((t, c), '')}" for c, ty in cols]
            out.append(f"TABLE {t}: {self.table_desc.get(t, '')}\n" + "\n".join(lines))
        return "\n\n".join(out)

    def metrics_block(self, rows: pd.DataFrame) -> str:
        if rows.empty:
            return "(no certified metric matched)"
        keep = ["metric_id", "metric_name", "business_definition", "formula", "grain", "time_basis",
                "default_filters", "unit", "certified_flag"]
        return "\n".join(" | ".join(f"{k}: {r[k]}" for k in keep if k in r.index) for _, r in rows.iterrows())
