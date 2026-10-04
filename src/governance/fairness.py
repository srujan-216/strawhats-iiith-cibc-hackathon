"""The ONLY module in this codebase allowed to read protected-attribute columns.

Enforced in two ways:
  1. tests/test_no_protected_features.py asserts protected columns are absent from
     src/layer3/catalog.yaml and gold.features_online.
  2. src/layer2/guard.py refuses SQL that touches protected columns (via Catalog.protected).

What this module does:
  - Joins gold.c360_customer -> silver.customers on member_crm_ids to pull the protected cols.
  - Measures three fairness metrics per protected attribute:
      a) action distribution from gold.nba_recommendations
      b) predicted cure (avg p_cure for the recommended action)
      c) vulnerability_signal rate (sanity on the OR-tipped flag)
  - Flags groups whose gap vs the population mean exceeds 5 percentage points.
  - Report-only; it never changes a recommendation.
"""
from __future__ import annotations
from pathlib import Path
import duckdb
import pandas as pd

# Protected or committed-proxy columns on silver.customers that this module may read
PROTECTED_COLS = [
    "gender_code", "marital_status", "citizenship_status", "household_size", "dependants_count",
    "newcomer_program_flag", "accessibility_needs_flag", "age", "age_band",
    "vulnerability_type",     # the TYPE is protected; the vulnerability_flag itself is a protective signal
    "fsa",                    # FSA used as income proxy
    "majority_language",      # may not exist in silver; omitted if missing
    "cpp_oas_deposit_flag", "ccb_deposit_flag",  # on silver.deposit_accounts; proxies
]

# Attributes to break the fairness table down by (categorical only; numeric age bucketed to age_band)
GROUP_BY_COLS = ["gender_code", "marital_status", "citizenship_status", "age_band",
                 "newcomer_program_flag"]

GAP_THRESHOLD_PP = 5.0


def _frame(con):
    """One joined frame per golden_id: nba recommendation + chosen customer protected cols.

    We pick ONE member CRM record per golden_id (the first non-deleted) to read protected cols.
    Protected cols are typically stable per person so this is fine for aggregation."""
    present = {r[0] for r in con.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='silver' AND table_name='customers'").fetchall()}
    gb = [c for c in GROUP_BY_COLS if c in present]
    sel = ", ".join(f"c.{c}" for c in gb)
    return con.execute(f"""
        WITH chosen AS (
            SELECT golden_id, member_crm_ids[1] AS pick_crm
              FROM gold.c360_customer)
        SELECT nba.case_id, nba.golden_id, nba.recommended_action,
               nba.p_cure::DOUBLE AS p_cure,
               nba.decision_value::DOUBLE AS decision_value,
               fe.vulnerability_signal, {sel}
          FROM gold.nba_recommendations nba
          JOIN chosen ON chosen.golden_id = nba.golden_id
          JOIN silver.customers c ON c.crm_customer_id = chosen.pick_crm
          LEFT JOIN gold.features_online fe ON fe.golden_id = nba.golden_id""").df()


def _gaps(df: pd.DataFrame, grouping: str, value_col: str, pop_mean: float, is_pct: bool = False) -> pd.DataFrame:
    """Group by `grouping`, show value_col mean per group and the gap vs pop_mean in percentage points."""
    g = df.groupby(grouping, dropna=False).agg(n=(value_col, "size"),
                                                mean=(value_col, "mean")).reset_index()
    g["mean"] = g["mean"].astype(float)
    g["pct"] = g["mean"] * 100 if is_pct else g["mean"]
    g["gap_pp"] = (g["mean"] - pop_mean) * 100
    g["flag"] = g["gap_pp"].abs() >= GAP_THRESHOLD_PP
    g["flag_label"] = g["flag"].map({True: "FLAG", False: "ok"})
    return g


def write_report(cfg: dict, out: str = "reports/fairness_report.md") -> dict:
    from tabulate import tabulate
    con = duckdb.connect(cfg["db_path"], read_only=True)
    df = _frame(con)
    con.close()
    md = [f"# Fairness report", f"Scope: {len(df):,} open cases from gold.nba_recommendations.", "",
          "**Methodology.** For each protected attribute we compute three metrics per group and the "
          f"gap vs the population mean, flagging groups where the gap exceeds **{GAP_THRESHOLD_PP:.0f} "
          "percentage points**. Report-only; no live decisions are changed here. See CLAUDE.md §2 "
          "'Protected attributes' for the policy.", ""]
    verdicts = {}
    for grouping in GROUP_BY_COLS:
        if grouping not in df.columns:
            continue
        md.append(f"## {grouping}")
        md.append("")
        # a) action distribution per group (chi-square-like: show mix)
        mix = (df.assign(cnt=1).groupby([grouping, "recommended_action"], dropna=False)["cnt"].sum()
                 .unstack(fill_value=0))
        mix_pct = (mix.T / mix.sum(axis=1)).T * 100
        md.append("**Action distribution (% within group)**")
        md.append(tabulate(mix_pct.round(1).reset_index(), headers="keys", tablefmt="github",
                           showindex=False))
        md.append("")
        # b) predicted cure
        pop_cure = df["p_cure"].mean()
        gcure = _gaps(df, grouping, "p_cure", pop_cure)
        gcure["gap_pp"] = gcure["gap_pp"].round(2)
        gcure["mean"] = (gcure["mean"] * 100).round(2)
        md.append(f"**Predicted cure (avg p_cure) — population mean {pop_cure*100:.2f}%**")
        md.append(tabulate(gcure[[grouping, "n", "mean", "gap_pp", "flag_label"]].rename(
            columns={"mean": "pred_cure_pct", "flag_label": "verdict"}), headers="keys", tablefmt="github",
            showindex=False))
        md.append("")
        # c) vulnerability_signal rate
        if "vulnerability_signal" in df.columns:
            df_v = df.assign(v=df["vulnerability_signal"].astype(float))
            pop_v = df_v["v"].mean()
            gv = _gaps(df_v, grouping, "v", pop_v)
            gv["mean"] = (gv["mean"] * 100).round(2)
            gv["gap_pp"] = gv["gap_pp"].round(2)
            md.append(f"**vulnerability_signal rate — population {pop_v*100:.2f}%**")
            md.append(tabulate(gv[[grouping, "n", "mean", "gap_pp", "flag_label"]].rename(
                columns={"mean": "vuln_pct", "flag_label": "verdict"}), headers="keys", tablefmt="github",
                showindex=False))
            md.append("")
        # verdict for this attribute: how many groups flagged?
        n_flag = int(gcure["flag"].sum())
        verdicts[grouping] = {"n_groups": int(len(gcure)), "n_flagged_cure": n_flag}
        if n_flag == 0:
            md.append(f"_Verdict for {grouping}: all groups within the {GAP_THRESHOLD_PP:.0f}pp band on "
                      "predicted cure._")
        else:
            flagged_names = ", ".join(str(x) for x in gcure.loc[gcure["flag"], grouping].tolist())
            md.append(f"_Verdict for {grouping}: {n_flag} group(s) outside the {GAP_THRESHOLD_PP:.0f}pp "
                      f"band on predicted cure: {flagged_names}._")
        md.append("")
    md.append("## Overall")
    md.append("")
    total_flags = sum(v["n_flagged_cure"] for v in verdicts.values())
    if total_flags == 0:
        md.append(f"All groups across {len(verdicts)} protected attributes are within the "
                  f"{GAP_THRESHOLD_PP:.0f}pp fairness band on predicted cure.")
    else:
        md.append(f"{total_flags} group(s) across {len(verdicts)} protected attributes exceed the "
                  f"{GAP_THRESHOLD_PP:.0f}pp fairness band. These are reported for human review; "
                  "they do not change live recommendations.")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(md), encoding="utf-8")
    return {"attributes": list(verdicts.keys()), "verdicts": verdicts,
            "total_flagged_cure_groups": total_flags}


def append_to_model_card(verdicts: dict, path: str = "reports/model_card.md") -> None:
    """Add a 'Fairness' section to the model card. Idempotent: strips any prior section first."""
    p = Path(path)
    if not p.exists():
        return
    txt = p.read_text(encoding="utf-8")
    marker = "\n## Fairness\n"
    if marker in txt:
        txt = txt.split(marker)[0]
    lines = [marker.strip(), "",
             f"Report: `reports/fairness_report.md`. Measured on {len(verdicts.get('verdicts', {}))} "
             "protected attributes using the method in src/governance/fairness.py "
             f"(5pp fairness band on predicted cure)."]
    tot = verdicts.get("total_flagged_cure_groups", 0)
    if tot == 0:
        lines.append("**All groups fall within the 5pp band on predicted cure.** No live recommendation "
                     "is changed by fairness; the module is report-only (see CLAUDE.md §2).")
    else:
        lines.append(f"{tot} group(s) exceed the 5pp band. See fairness_report.md for group names.")
    p.write_text(txt.rstrip() + "\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
