"""Data quality report: silver fix_log + gold.dq_results + match counts -> one markdown.

  python run.py dq-report

The output is a single table (one row per issue) that an auditor can read: issue, table, records
affected, how handled. Nothing is computed inside this module except pull / stitch / format."""
from __future__ import annotations
import time
from pathlib import Path
import duckdb


# curated map silver.fix_log rule -> (short description, how handled)
_SILVER_ROLLUP = {
    "cif_left_pad_10:src_customer_ref":
        ("deposit CIF left-padded to 10 digits", "padded in silver.deposit_accounts"),
    "flag:cif_padded":
        ("deposits with lost leading zeros detected", "silver flag cif_padded; CIF padded"),
    "dob_ambiguous_day_month:dob_alt":
        ("CRM DOB with both DD/MM and MM/DD interpretations", "both readings kept (dob_parsed + dob_alt)"),
    "dob_parse:dob_parsed":
        ("CRM DOB parsed from mixed formats", "ISO date in dob_parsed"),
    "flag:dob_ambiguous":
        ("CRM DOB ambiguous day/month", "silver flag dob_ambiguous; both readings kept"),
    "flag:repaired_DFI0812":
        ("DFI-0812 shifted-column bureau rows", "4 inquiry columns rotated back; dfi0812_as_loaded keeps the originals"),
    "flag:orphan_case":
        ("contact_history rows with case_id not in collections_cases", "silver flag orphan_case; see DC-COLL-001 Q7 check"),
    "schema_drift_channel_v2_coalesced:channel":
        ("contact_history.channel_v2 after REL-0926 release", "coalesced into one channel column, old column dropped"),
    "flag:channel_from_v2": ("contact_history rows carrying channel from channel_v2", "silver flag channel_from_v2"),
    "flag:cdc_deleted": ("CRM records marked deleted (cdc_operation='D')", "silver flag cdc_deleted; still carried, excluded from live surrogate choice"),
    "exact_duplicate_removed": ("contact_history exact duplicate rows", "deduped; silver.contact_history_duplicates records the kept id"),
    "flag:phone_invalid": ("CRM primary phone fails NANP validation", "silver flag phone_invalid; left NULL in e164 column"),
    "flag:phone_masked": ("card_accounts phone comes partially masked by source", "pattern kept in cardholder_phone_mask"),
    "flag:stale_snapshot": ("card/loan/deposit rows with snapshot_date before 2026-09-28", "silver flag stale_snapshot (closed / written-off accounts)"),
    "province_code_standardise:province_code": ("CRM province_code variants (Ont., B.C., ...)", "normalised to 2-letter code"),
    "na_placeholder_to_null:note_text": ("agent_notes NA/N/A/na/- placeholder bodies", "set to NULL; original kept in note_placeholder"),
    "na_placeholder_to_null:middle_name": ("CRM middle_name 'X' placeholder", "set to NULL"),
    "email_lower_trim:email": ("mixed-case emails on CRM", "lower-cased and trimmed"),
    "phone_e164_from_raw:primary_phone_e164": ("CRM primary phone normalised to +1 E.164", "built from raw digits where valid NANP"),
    "phone_e164_from_raw:secondary_phone_e164": ("CRM secondary phone normalised to +1 E.164", "built from raw digits"),
    "phone_e164_from_raw:work_phone_e164": ("CRM work phone normalised to +1 E.164", "built from raw digits"),
    "phone_e164_from_raw:holder_phone_e164": ("deposit holder phone normalised to +1 E.164", "built from raw digits"),
    "phone_e164_from_raw:borrower_phone_e164": ("loan borrower phone normalised to +1 E.164", "built from raw digits"),
    "phone_e164_from_raw:cardholder_phone_e164": ("card holder phone normalised to +1 E.164", "built from raw digits where unmasked"),
    "postal_code_from_raw:cardholder_postal": ("cardholder postal code normalised to A1A 1A1", "space inserted, O/I -> 0/1 at digit positions"),
    "dob_parse:cardholder_dob": ("card DOB (DD-MM-YYYY) parsed", "parsed to DATE"),
    "dob_parse:borrower_dob": ("loan DOB (YYYY/MM/DD) parsed", "parsed to DATE"),
    "dob_parse:holder_dob": ("deposit DOB (YYYYMMDD) parsed", "parsed to DATE"),
    "repair_DFI0812_inquiry_rotation:inquiries_hard_3m":
        ("DFI-0812: hard_3m value was the soft_12m value", "rotated back"),
    "repair_DFI0812_inquiry_rotation:inquiries_hard_6m":
        ("DFI-0812: hard_6m value was the hard_3m value", "rotated back"),
    "repair_DFI0812_inquiry_rotation:inquiries_hard_12m":
        ("DFI-0812: hard_12m value was the hard_6m value", "rotated back"),
    "repair_DFI0812_inquiry_rotation:inquiries_soft_12m":
        ("DFI-0812: soft_12m value was the hard_12m value", "rotated back"),
}


def write_dq_report(cfg: dict, out: str = "reports/data_quality_report.md") -> str:
    from tabulate import tabulate
    con = duckdb.connect(cfg["db_path"], read_only=True)
    sections = []

    # 1. silver cleaning issues (latest run per rule)
    # one row per rule from the latest run_id PER TABLE: older rule-name spellings don't appear
    silver = con.execute("""
        WITH latest_full AS (
            SELECT table_name, max(run_id) AS run_id FROM silver.fix_log
             WHERE sample_n IS NULL GROUP BY table_name),
        latest_any AS (
            SELECT table_name, max(run_id) AS run_id FROM silver.fix_log GROUP BY table_name),
        latest AS (
            SELECT table_name, coalesce(f.run_id, a.run_id) AS run_id
              FROM latest_any a LEFT JOIN latest_full f USING (table_name))
        SELECT f.table_name, f.rule, f.rows_affected, f.rows_in
          FROM silver.fix_log f JOIN latest USING (table_name, run_id)
         WHERE f.rows_affected > 0 ORDER BY f.table_name, f.rule""").fetchall()
    rows = []
    for t, rule, n, n_in in silver:
        if rule.startswith("dc_coll_001"):
            continue   # Q7 reports this on its own
        issue, handled = _SILVER_ROLLUP.get(rule, (rule, "see silver.fix_log"))
        rows.append((t, issue, f"{n:,}", f"{100*n/max(n_in,1):.2f}% of rows", handled))
    sections.append(("## 1. Silver cleaning (one row per rule, latest full run)",
                     ["table", "issue", "records affected", "share", "how handled"], rows))

    # 2. gold quality checks
    gold = con.execute("""SELECT check_id, scope, records, failing, rule, status FROM gold.dq_results
                          ORDER BY check_id""").fetchall()
    sections.append(("## 2. Gold C360 quality checks",
                     ["id", "scope", "records", "failing", "rule", "status"],
                     [(c, s, f"{r:,}", f"{f:,}", rule, status) for c, s, r, f, rule, status in gold]))

    # 3. identity resolution summary (lifted from reports/match_report.md if present)
    match = Path("reports/match_report.md")
    if match.exists():
        head = []
        for line in match.read_text(encoding="utf-8").splitlines():
            if line.startswith("## Example"):
                break
            if line:
                head.append(line)
        sections.append(("## 3. Identity resolution summary (from match report)", None, "\n".join(head)))

    body = [f"# Data quality report", f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
    for h, headers, data in sections:
        body.append(h)
        body.append("")
        if headers is None:
            body.append(data)
        else:
            body.append(tabulate(data, headers=headers, tablefmt="github") if data else "(no issues)")
        body.append("")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(body), encoding="utf-8")
    con.close()
    return out
