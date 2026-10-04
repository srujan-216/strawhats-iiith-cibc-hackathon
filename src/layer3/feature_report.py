"""reports/feature_report.md: coverage, correlation with the cure proxy, pairwise correlation
pruning, and the kept list. Target is a proxy (any-case cured) until Layer 4 fixes it per
decision_date; column names and recipe link back to src/layer3/catalog.yaml."""
from __future__ import annotations
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
from src.layer3.features import NUMERIC_COLUMNS, TEXT_COLUMNS


def _target(con):
    """Proxy target: any case cured for the customer. Replaced by Layer 4 PIT target later."""
    con.execute("""CREATE OR REPLACE TEMP TABLE _tgt AS
        SELECT xc.golden_id, bool_or(coalesce(cc.cure_flag, false))::INTEGER AS cured
          FROM silver.collections_cases cc
          JOIN silver.id_xref xc ON xc.source_system='collections' AND xc.source_key = cc.case_id
         GROUP BY xc.golden_id""")


def _numeric_arr(df, col):
    s = df[col]
    if s.dtype == bool: s = s.astype(float)
    elif s.dtype.kind in "OU":
        # categorical features: use any-non-default as a proxy; small IV approximation only
        default = {"txt_hardship_signal": "none", "txt_delay_reason": "unknown", "txt_sentiment": "neutral"}
        s = (s != default.get(col, s.mode(dropna=False).iloc[0])).astype(float)
    return pd.to_numeric(s, errors="coerce")


def build_report(cfg: dict, out: str = "reports/feature_report.md") -> str:
    from tabulate import tabulate
    con = duckdb.connect(cfg["db_path"])
    _target(con)
    cols = NUMERIC_COLUMNS + TEXT_COLUMNS
    df = con.execute(f"""SELECT f.*, coalesce(t.cured, 0) AS cured
                         FROM gold.features_online f LEFT JOIN _tgt t USING (golden_id)""").df()
    rows = []
    for c in cols:
        s = _numeric_arr(df, c)
        cov = 100 * s.notna().mean()
        try:
            r = s.fillna(s.median() if s.dtype.kind == "f" else 0).corr(df["cured"])
            r = round(float(r), 3) if pd.notna(r) else None
        except Exception:
            r = None
        rows.append({"feature": c, "coverage_pct": round(cov, 1), "corr_cured": r})
    rep_rows = sorted(rows, key=lambda r: -(abs(r["corr_cured"] or 0)))

    # pairwise correlation prune (|r| > 0.9 between numeric features)
    num_df = pd.DataFrame({c: _numeric_arr(df, c) for c in NUMERIC_COLUMNS})
    mat = num_df.fillna(num_df.median(numeric_only=True)).corr()
    high = []
    for i, a in enumerate(NUMERIC_COLUMNS):
        for b in NUMERIC_COLUMNS[i + 1:]:
            r = mat.loc[a, b]
            if pd.notna(r) and abs(r) > 0.9:
                high.append((a, b, round(float(r), 3)))

    md = [f"# Feature report ({len(df):,} customers)", "",
          "Target used here is a proxy: `cured` = any of the customer's collections cases cured. "
          "Layer 4 (P6) replaces this with a point-in-time target per decision_date (cured within 30 days). "
          "Correlations are a quick sanity check, not a model selection.", "",
          "## Coverage and correlation with cured proxy (sorted by |corr|)", "",
          tabulate(rep_rows, headers="keys", tablefmt="github"), "",
          "## Pairwise correlation prune (|r| > 0.9)", ""]
    md.append(tabulate(high, headers=["feature_a", "feature_b", "r"], tablefmt="github") if high
              else "(no numeric pair above threshold - no pruning needed)")
    # P6 (uplift model) is the real selector via SHAP + uplift importance. The proxy here biases
    # against low-coverage behavioural features that only move once a case opens, so we keep all
    # features in the store and let the trained model prune.
    kept = [r["feature"] for r in rows]
    dropped = []
    md += ["", f"## Kept list ({len(kept)} of {len(rows)} features)", "",
           ", ".join(kept),
           "", "## Dropped",
           tabulate(dropped, headers="keys", tablefmt="github") if dropped
           else "(none - all features kept)",
           "", "## Notes",
           "- IV / PSI left to a point-in-time build with a real target; the proxy here is biased by the "
             "order of case opens.",
           "- bureau_delta_90d coverage ~48% is by design (CLAUDE §bureau coverage); the companion "
             "`bureau_present` flag lets the model treat missingness explicitly.",
           "- Protected or proxy columns (gender, age, FSA income, majority_language, cpp_oas, ccb) do NOT "
             "appear here; src/governance/fairness.py is the only module allowed to read them."]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(md), encoding="utf-8")
    con.close()
    return out
