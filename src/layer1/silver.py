"""Layer 1, step 1: silver tables (cleaned, typed, deduplicated, every change logged).

  python run.py silver [--sample N]

For each source table: stage main.<t> (optionally restricted to a customer-level sample), apply the
rules below in DuckDB SQL, write silver.<t>, and log every rule to
silver.fix_log(table_name, rule, rows_affected, rows_in, example_before, example_after, run_ts, sample_n).

Rules (see docs/DATA_NOTES.md for the evidence behind each one):
  dates      each system's DOB format parsed; CRM day/month-ambiguous DOBs keep both readings
  ids        deposit CIF left-padded to 10 digits; ids always text
  contact    phones -> E.164, postal codes -> 'A1A 1A1', emails lower/trim, provinces/codes upper
  na         placeholders that mean "missing" -> NULL; real codes such as outcome_code 'NA' kept
  cdc        current version per key; CRM deletes kept with is_deleted = true
  dedupe     exact duplicates (all columns except key/lineage) removed, survivor recorded;
             latest snapshot per account
  drift      contact_history.channel_v2 (REL-0926) coalesced into channel
  DFI-0812   bureau rows with the four inquiry columns rotated by one are detected and repaired
  orphans    contacts whose case_id is not in collections_cases kept and flagged

Raw columns are never overwritten when a cleaned value is derived from them: the cleaned value goes in
a new column (e.g. cardholder_phone_raw -> cardholder_phone_e164). Nothing is dropped silently: removed
duplicates go to silver.<t>_duplicates with the id of the row that was kept.
"""
from __future__ import annotations
import time
import duckdb
from src.common.sample import build_sample, sample_filter

SNAPSHOT_DATE = "2026-09-28"

# ---------------------------------------------------------------------------------------------- macros
MACROS = r"""
CREATE OR REPLACE MACRO only_digits(x) AS regexp_replace(x, '[^0-9]', '', 'g');

-- North American number -> +1XXXXXXXXXX; masked (x / *), wrong length or an area code starting with
-- 0/1 -> NULL (catches truncated 9-digit numbers written with a +1 prefix: '+1 204 889 694')
CREATE OR REPLACE MACRO nanp10(d) AS (CASE WHEN regexp_full_match(d, '[2-9][0-9]{9}') THEN '+1' || d END);
CREATE OR REPLACE MACRO norm_phone(x) AS (
    CASE WHEN x IS NULL OR regexp_matches(x, '[xX*]') THEN NULL
         WHEN length(only_digits(x)) = 10 THEN nanp10(only_digits(x))
         WHEN length(only_digits(x)) = 11 AND starts_with(only_digits(x), '1') THEN nanp10(substr(only_digits(x), 2))
         ELSE NULL END);

-- masked card phones ('819364xxx00') kept as a digit/x pattern for partial matching
CREATE OR REPLACE MACRO phone_mask(x) AS (
    CASE WHEN regexp_matches(x, '[xX*]') THEN lower(regexp_replace(x, '[^0-9xX*]', '', 'g')) END);

-- digit positions 2/4/6: O->0 and I->1 (OCR / keying errors); then strict A1A 1A1
CREATE OR REPLACE MACRO postal_compact(x) AS upper(regexp_replace(x, '[^A-Za-z0-9]', '', 'g'));
CREATE OR REPLACE MACRO postal_digit(c) AS (CASE c WHEN 'O' THEN '0' WHEN 'I' THEN '1' ELSE c END);
CREATE OR REPLACE MACRO postal_fixed(s) AS (
    substr(s, 1, 1) || postal_digit(substr(s, 2, 1)) || substr(s, 3, 1)
    || postal_digit(substr(s, 4, 1)) || substr(s, 5, 1) || postal_digit(substr(s, 6, 1)));
CREATE OR REPLACE MACRO norm_postal(x) AS (
    CASE WHEN x IS NULL THEN NULL
         WHEN regexp_full_match(postal_fixed(postal_compact(x)), '[A-Z][0-9][A-Z][0-9][A-Z][0-9]')
         THEN substr(postal_fixed(postal_compact(x)), 1, 3) || ' ' || substr(postal_fixed(postal_compact(x)), 4, 3)
         ELSE NULL END);

CREATE OR REPLACE MACRO norm_email(x) AS nullif(lower(trim(x)), '');

CREATE OR REPLACE MACRO norm_province(x) AS (
    CASE upper(regexp_replace(trim(x), '[. ]', '', 'g'))
        WHEN 'ONT' THEN 'ON' WHEN 'ONTARIO' THEN 'ON'
        WHEN 'QUE' THEN 'QC' WHEN 'QUEBEC' THEN 'QC' WHEN 'PQ' THEN 'QC'
        WHEN 'ALTA' THEN 'AB' WHEN 'ALBERTA' THEN 'AB'
        WHEN 'MAN' THEN 'MB' WHEN 'MANITOBA' THEN 'MB'
        WHEN 'SASK' THEN 'SK' WHEN 'NFLD' THEN 'NL' WHEN 'PEI' THEN 'PE'
        ELSE upper(regexp_replace(trim(x), '[. ]', '', 'g')) END);

CREATE OR REPLACE MACRO pad_cif(x) AS (
    CASE WHEN regexp_full_match(x, '[0-9]{1,10}') THEN lpad(x, 10, '0') ELSE x END);

-- CRM dob_raw: 'YYYY-MM-DD' | 'NN/NN/YYYY' (both DD/MM and MM/DD occur) | 'Mon DD YYYY'
CREATE OR REPLACE MACRO dob_dm(x) AS try_strptime(x, '%d/%m/%Y')::DATE;
CREATE OR REPLACE MACRO dob_md(x) AS try_strptime(x, '%m/%d/%Y')::DATE;
CREATE OR REPLACE MACRO crm_dob_ambiguous(x) AS
    coalesce(x LIKE '%/%' AND dob_dm(x) IS NOT NULL AND dob_md(x) IS NOT NULL AND dob_dm(x) <> dob_md(x), false);
-- best guess: CRM's own parsed date_of_birth when it is one of the two readings, else day-first
-- (day-first is the more common unambiguous convention: 122,353 vs 91,531 rows)
CREATE OR REPLACE MACRO crm_dob_best(x, crm_dob) AS (
    CASE WHEN x IS NULL THEN NULL
         WHEN regexp_full_match(x, '[0-9]{4}-[0-9]{2}-[0-9]{2}') THEN try_strptime(x, '%Y-%m-%d')::DATE
         WHEN x LIKE '%/%' THEN
             CASE WHEN crm_dob_ambiguous(x) THEN (CASE WHEN crm_dob = dob_md(x) THEN dob_md(x) ELSE dob_dm(x) END)
                  ELSE coalesce(dob_dm(x), dob_md(x)) END
         ELSE try_strptime(x, '%b %d %Y')::DATE END);
CREATE OR REPLACE MACRO crm_dob_alt(x, crm_dob) AS (
    CASE WHEN crm_dob_ambiguous(x) THEN
        (CASE WHEN crm_dob_best(x, crm_dob) = dob_dm(x) THEN dob_md(x) ELSE dob_dm(x) END) END);
"""

# DFI-0812: the bureau file was loaded with the four inquiry columns rotated one place to the right
# (soft_12m's value landed in hard_3m). A 3-month count can never exceed the 6-month count, which
# finds the rotated rows; rotating back yields 3m <= 6m <= 12m for every detected row.
DFI0812_DETECT = "inquiries_hard_3m > inquiries_hard_6m"
DFI0812_REPAIR = {   # repaired column <- column it was loaded into
    "inquiries_hard_3m": "inquiries_hard_6m",
    "inquiries_hard_6m": "inquiries_hard_12m",
    "inquiries_hard_12m": "inquiries_soft_12m",
    "inquiries_soft_12m": "inquiries_hard_3m",
}

LINEAGE_COLS = {"batch_id", "extract_ts", "record_hash", "file_received_ts"}
NOTE_PLACEHOLDERS = "('NA', 'N/A', 'na', 'n/a', '-')"   # 'LM' (left message) and 'MV' are kept: they carry meaning

# ------------------------------------------------------------------------------------------- table specs
# replace: column -> (rule, new expression)            (column keeps its name; old value logged)
# add:     column -> (rule, expression, source column)  (new column; rows logged = rows where it changes)
# flags:   (dq flag, condition)
# info:    (rule, condition)  logged only, nothing changed (e.g. 'NA' kept as a real value)
SPECS: dict[str, dict] = {
    "customers": dict(
        pk="crm_customer_id", latest="effective_from_ts DESC, extract_ts DESC", cdc=True,
        exclude_from_dupe={"customer_uuid"},
        replace={
            "email": ("email_lower_trim", "norm_email(email)"),
            "province_code": ("province_code_standardise", "norm_province(province_code)"),
            "postal_code": ("postal_code_from_raw", "norm_postal(postal_code_raw)"),
            "primary_phone_e164": ("phone_e164_from_raw", "norm_phone(primary_phone_raw)"),
            "middle_name": ("na_placeholder_to_null", "CASE WHEN middle_name = 'X' THEN NULL ELSE middle_name END"),
        },
        add={
            "dob_parsed": ("dob_parse", "crm_dob_best(dob_raw, date_of_birth)", "dob_raw"),
            "dob_alt": ("dob_ambiguous_day_month", "crm_dob_alt(dob_raw, date_of_birth)", "dob_raw"),
            "dob_ambiguous": (None, "crm_dob_ambiguous(dob_raw)", None),
            "secondary_phone_e164": ("phone_e164_from_raw", "norm_phone(secondary_phone_raw)", "secondary_phone_raw"),
            "work_phone_e164": ("phone_e164_from_raw", "norm_phone(work_phone_raw)", "work_phone_raw"),
            "is_deleted": (None, "coalesce(cdc_operation = 'D', false)", None),
        },
        flags=[
            ("dob_ambiguous", "crm_dob_ambiguous(dob_raw)"),
            ("dob_unparseable", "dob_raw IS NOT NULL AND crm_dob_best(dob_raw, date_of_birth) IS NULL"),
            ("phone_invalid", "primary_phone_raw IS NOT NULL AND norm_phone(primary_phone_raw) IS NULL"),
            ("postal_invalid", "postal_code_raw IS NOT NULL AND norm_postal(postal_code_raw) IS NULL"),
            ("cdc_deleted", "cdc_operation = 'D'"),
        ],
        info=[("na_kept_as_real_first_name", "first_name = 'NA'")],
    ),
    "card_accounts": dict(
        pk="card_account_id", latest="snapshot_date DESC, extract_ts DESC",
        add={
            "cardholder_dob": ("dob_parse", "try_strptime(cardholder_dob_raw, '%d-%m-%Y')::DATE", "cardholder_dob_raw"),
            "cardholder_phone_e164": ("phone_e164_from_raw", "norm_phone(cardholder_phone_raw)", "cardholder_phone_raw"),
            "cardholder_phone_mask": ("phone_masked_kept_as_pattern", "phone_mask(cardholder_phone_raw)", "cardholder_phone_raw"),
            "cardholder_postal": ("postal_code_from_raw", "norm_postal(cardholder_postal_raw)", "cardholder_postal_raw"),
        },
        flags=[
            ("dob_unparseable", "cardholder_dob_raw IS NOT NULL AND try_strptime(cardholder_dob_raw, '%d-%m-%Y') IS NULL"),
            ("phone_masked", "phone_mask(cardholder_phone_raw) IS NOT NULL"),
            ("phone_invalid", "cardholder_phone_raw IS NOT NULL AND phone_mask(cardholder_phone_raw) IS NULL AND norm_phone(cardholder_phone_raw) IS NULL"),
            ("postal_invalid", "cardholder_postal_raw IS NOT NULL AND norm_postal(cardholder_postal_raw) IS NULL"),
            ("stale_snapshot", f"snapshot_date < DATE '{SNAPSHOT_DATE}'"),
        ],
    ),
    "loan_accounts": dict(
        pk="loan_id", latest="snapshot_date DESC, extract_ts DESC",
        add={
            "borrower_dob": ("dob_parse", "try_strptime(borrower_dob_raw, '%Y/%m/%d')::DATE", "borrower_dob_raw"),
            "borrower_phone_e164": ("phone_e164_from_raw", "norm_phone(borrower_phone_raw)", "borrower_phone_raw"),
            "borrower_postal": ("postal_code_from_raw", "norm_postal(borrower_postal_raw)", "borrower_postal_raw"),
        },
        flags=[
            ("dob_unparseable", "borrower_dob_raw IS NOT NULL AND try_strptime(borrower_dob_raw, '%Y/%m/%d') IS NULL"),
            ("phone_invalid", "borrower_phone_raw IS NOT NULL AND norm_phone(borrower_phone_raw) IS NULL"),
            ("postal_invalid", "borrower_postal_raw IS NOT NULL AND norm_postal(borrower_postal_raw) IS NULL"),
            ("stale_snapshot", f"snapshot_date < DATE '{SNAPSHOT_DATE}'"),
        ],
    ),
    "deposit_accounts": dict(
        pk="deposit_account_id", latest="snapshot_date DESC, extract_ts DESC",
        replace={
            "src_customer_ref": ("cif_left_pad_10", "pad_cif(src_customer_ref)"),
            "joint_holder_ref": ("cif_left_pad_10", "pad_cif(joint_holder_ref)"),
        },
        add={
            "holder_dob": ("dob_parse", "try_strptime(holder_dob_raw, '%Y%m%d')::DATE", "holder_dob_raw"),
            "holder_phone_e164": ("phone_e164_from_raw", "norm_phone(holder_phone_raw)", "holder_phone_raw"),
            "holder_postal": ("postal_code_from_raw", "norm_postal(holder_postal_raw)", "holder_postal_raw"),
        },
        flags=[
            ("cif_padded", "src_customer_ref IS DISTINCT FROM pad_cif(src_customer_ref)"),
            ("dob_unparseable", "holder_dob_raw IS NOT NULL AND try_strptime(holder_dob_raw, '%Y%m%d') IS NULL"),
            ("phone_invalid", "holder_phone_raw IS NOT NULL AND norm_phone(holder_phone_raw) IS NULL"),
            ("postal_invalid", "holder_postal_raw IS NOT NULL AND norm_postal(holder_postal_raw) IS NULL"),
            ("stale_snapshot", f"snapshot_date < DATE '{SNAPSHOT_DATE}'"),
        ],
    ),
    "collections_cases": dict(pk="case_id", latest="extract_ts DESC"),
    "contact_history": dict(
        pk="contact_id", latest="extract_ts DESC", drop={"channel_v2"},
        referenced_by=["agent_notes", "promises_to_pay", "call_transcripts"],
        replace={"channel": ("schema_drift_channel_v2_coalesced", "coalesce(channel_v2, channel)")},
        flags=[
            ("channel_from_v2", "channel_v2 IS NOT NULL"),
            ("orphan_case", "case_id IS NOT NULL AND case_id NOT IN (SELECT case_id FROM main.collections_cases)"),
        ],
        info=[("na_kept_as_code_no_answer", "outcome_code = 'NA'")],
        keep_codes_as_is={"treatment_code"},   # canonical values are lower case ('outbound_call')
    ),
    "promises_to_pay": dict(pk="ptp_id", latest="status_ts DESC NULLS LAST"),
    "agent_notes": dict(
        pk="note_id", latest="last_edited_ts DESC NULLS LAST",
        replace={"note_text": ("na_placeholder_to_null",
                               f"CASE WHEN trim(note_text) IN {NOTE_PLACEHOLDERS} THEN NULL ELSE note_text END")},
        add={"note_placeholder": (None, f"CASE WHEN trim(note_text) IN {NOTE_PLACEHOLDERS} THEN note_text END", None)},
        flags=[("note_placeholder", f"trim(note_text) IN {NOTE_PLACEHOLDERS}")],
    ),
    "external": dict(
        pk="bureau_request_id", latest="file_received_ts DESC", extract_expr="file_received_ts",
        replace={**{c: (f"repair_DFI0812_inquiry_rotation:{c}", f"CASE WHEN {DFI0812_DETECT} THEN {src} ELSE {c} END")
                    for c, src in DFI0812_REPAIR.items()},
                 "bank_subject_ref": ("cif_left_pad_10", "pad_cif(bank_subject_ref)")},
        add={"dfi0812_as_loaded": (None, f"CASE WHEN {DFI0812_DETECT} THEN '[' || concat_ws(',', "
                                         + ", ".join(DFI0812_REPAIR) + ") || ']' END", None)},
        flags=[("repaired_DFI0812", DFI0812_DETECT)],
    ),
}
TABLES = list(SPECS)


# ------------------------------------------------------------------------------------------------ build
def _q(c: str) -> str:
    return '"' + c.replace('"', '""') + '"'


def _columns(con, table: str, schema: str = "main") -> list[tuple[str, str]]:
    return con.execute("SELECT column_name, data_type FROM information_schema.columns "
                       "WHERE table_schema=? AND table_name=? ORDER BY ordinal_position", [schema, table]).fetchall()


def _code_columns(cols, spec) -> dict:
    """Upper-case/trim every *_code text column not already handled (keeps canonical lower-case ones)."""
    skip = set(spec.get("replace", {})) | spec.get("keep_codes_as_is", set())
    return {c: ("code_upper_trim", f"upper(trim({_q(c)}))") for c, t in cols
            if c.endswith("_code") and t == "VARCHAR" and c not in skip}


def _log(con, run, table, rule, rows, rows_in, before=None, after=None):
    con.execute("INSERT INTO silver.fix_log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [run["run_ts"], table, rule, int(rows or 0), int(rows_in),
                 None if before is None else str(before)[:200], None if after is None else str(after)[:200],
                 run["sample_n"], run["run_id"]])


def build_table(con, t: str, run: dict, sample_n: int | None, log=print) -> dict:
    spec = SPECS[t]
    t0 = time.time()
    cols = _columns(con, t)
    names = [c for c, _ in cols]
    pk = spec["pk"]
    replace = {**_code_columns(cols, spec), **spec.get("replace", {})}
    add = spec.get("add", {})

    # 1. stage (sample restriction applied here)
    con.execute(f"CREATE OR REPLACE TEMP TABLE stg AS SELECT * FROM main.{t} WHERE {sample_filter(t, n=sample_n)}")
    n_in = con.execute("SELECT count(*) FROM stg").fetchone()[0]

    # 2. log value-level rules from the staged rows (one aggregate query)
    checks = []   # (rule, changed-condition, before, after)
    for c, (rule, expr) in replace.items():
        checks.append((rule if ":" in rule else f"{rule}:{c}",
                       f"{_q(c)} IS DISTINCT FROM ({expr})", _q(c), f"({expr})"))
    for c, (rule, expr, src) in add.items():
        if rule and src:
            checks.append((f"{rule}:{c}",
                           f"{_q(src)} IS NOT NULL AND ({expr}) IS NOT NULL AND {_q(src)} IS DISTINCT FROM CAST(({expr}) AS VARCHAR)",
                           _q(src), f"({expr})"))
    for flag, cond in spec.get("flags", []):
        checks.append((f"flag:{flag}", cond, None, None))
    for rule, cond in spec.get("info", []):
        checks.append((f"info:{rule}", cond, None, None))
    if checks:
        parts = []
        for _, cond, b, a in checks:
            parts += [f"count(*) FILTER (WHERE {cond})",
                      f"CAST(any_value({b}) FILTER (WHERE {cond}) AS VARCHAR)" if b else "NULL",
                      f"CAST(any_value({a}) FILTER (WHERE {cond}) AS VARCHAR)" if a else "NULL"]
        res = con.execute(f"SELECT {', '.join(parts)} FROM stg").fetchone()
        for i, (rule, *_rest) in enumerate(checks):
            n, b, a = res[3 * i: 3 * i + 3]
            if n or not rule.startswith("code_upper_trim"):
                _log(con, run, t, rule, n, n_in, b, a)

    # 3. transform: replaced columns, added columns, dq_flags, lineage
    select = []
    for c in names:
        if c in spec.get("drop", set()):
            continue
        select.append(f"({replace[c][1]}) AS {_q(c)}" if c in replace else _q(c))
    select += [f"({expr}) AS {_q(c)}" for c, (_, expr, _src) in add.items()]
    flag_list = ", ".join(f"CASE WHEN {cond} THEN '{flag}' END" for flag, cond in spec.get("flags", []))
    select.append(f"list_filter([{flag_list}]::VARCHAR[], x -> x IS NOT NULL) AS dq_flags" if flag_list
                  else "[]::VARCHAR[] AS dq_flags")
    select.append(f"'data/{t}.csv' AS source_file")
    if "extract_ts" not in names:   # lineage: when the source extract was produced
        select.append(spec.get("extract_expr", "try_strptime(regexp_extract(batch_id, '([0-9]{8})', 1), '%Y%m%d')")
                      + " AS extract_ts")
    con.execute(f"CREATE OR REPLACE TEMP TABLE xf0 AS SELECT {', '.join(select)} FROM stg")

    # 4. one row per key (CDC current version / latest snapshot)
    n_xf = n_in
    con.execute(f"""CREATE OR REPLACE TEMP TABLE xf1 AS SELECT * FROM xf0
                    QUALIFY row_number() OVER (PARTITION BY {_q(pk)} ORDER BY {spec['latest']}) = 1""")
    n_key = con.execute("SELECT count(*) FROM xf1").fetchone()[0]
    _log(con, run, t, "cdc_current_version_per_key" if spec.get("cdc") else "latest_snapshot_per_key",
         n_xf - n_key, n_in)

    # 5. exact duplicates: identical in every column except key and lineage
    excl = {pk, "dq_flags", "source_file"} | LINEAGE_COLS | spec.get("exclude_from_dupe", set())
    dcols = [r[0] for r in con.execute("DESCRIBE xf1").fetchall() if r[0] not in excl]
    h = "md5(concat_ws('|', " + ", ".join(f"coalesce(CAST({_q(c)} AS VARCHAR), '~')" for c in dcols) + "))"
    ref = "false"
    if spec.get("referenced_by"):
        ref = f"{_q(pk)} IN (" + " UNION ".join(f"SELECT {_q(pk)} FROM main.{r} WHERE {_q(pk)} IS NOT NULL"
                                               for r in spec["referenced_by"]) + ")"
    con.execute(f"""CREATE OR REPLACE TEMP TABLE xf AS
        WITH hashed AS (SELECT *, {h} AS _h, ({ref}) AS _ref FROM xf1)
        SELECT *, row_number() OVER (PARTITION BY _h ORDER BY _ref DESC, {_q(pk)}) AS _rn,
               first_value({_q(pk)}) OVER (PARTITION BY _h ORDER BY _ref DESC, {_q(pk)}) AS _survivor
        FROM hashed""")
    # a duplicate that other tables reference is kept (flagged) so no reference breaks
    con.execute(f"""CREATE OR REPLACE TABLE silver.{t}_duplicates AS
        SELECT {_q(pk)} AS removed_id, _survivor AS kept_id, '{run['run_ts']}'::TIMESTAMP AS run_ts
        FROM xf WHERE _rn > 1 AND NOT _ref""")
    n_dup = con.execute(f"SELECT count(*) FROM silver.{t}_duplicates").fetchone()[0]
    ex = con.execute(f"SELECT removed_id, kept_id FROM silver.{t}_duplicates LIMIT 1").fetchone()
    _log(con, run, t, "exact_duplicate_removed", n_dup, n_in, ex and ex[0], ex and f"kept {ex[1]}")
    n_dup_ref = con.execute("SELECT count(*) FROM xf WHERE _rn > 1 AND _ref").fetchone()[0]
    if n_dup_ref:
        _log(con, run, t, "exact_duplicate_kept_referenced", n_dup_ref, n_in)
    con.execute(f"""CREATE OR REPLACE TABLE silver.{t} AS
        SELECT * EXCLUDE (_h, _ref, _rn, _survivor, dq_flags),
               CASE WHEN _rn > 1 THEN list_append(dq_flags, 'duplicate_referenced') ELSE dq_flags END AS dq_flags
        FROM xf WHERE _rn = 1 OR _ref""")
    n_out = con.execute(f"SELECT count(*) FROM silver.{t}").fetchone()[0]
    for tmp_t in ("stg", "xf0", "xf1", "xf"):
        con.execute(f"DROP TABLE IF EXISTS {tmp_t}")
    secs = time.time() - t0
    log(f"  {t:<20} in {n_in:>10,}  out {n_out:>10,}  removed {n_in - n_out:>8,}  {secs:6.1f}s")
    return {"table": t, "rows_in": n_in, "rows_out": n_out, "seconds": round(secs, 1)}


def run_silver(cfg: dict, sample_n: int | None = None, tables: list[str] | None = None, log=print) -> list[dict]:
    t0 = time.time()
    con = duckdb.connect(cfg["db_path"])
    tmp = str((__import__("pathlib").Path(cfg["db_path"]).parent / "tmp").resolve())
    scfg = cfg.get("silver", {})   # laptop: small limits (spills to disk); GPU workstation: raise them
    con.execute(f"SET temp_directory='{tmp}'; SET memory_limit='{scfg.get('memory_limit', '4GB')}'; "
                f"SET threads={int(scfg.get('threads', 4))}; SET preserve_insertion_order=false;")
    con.execute(MACROS)
    con.execute("CREATE SCHEMA IF NOT EXISTS silver")
    con.execute("""CREATE TABLE IF NOT EXISTS silver.fix_log (run_ts TIMESTAMP, table_name VARCHAR, rule VARCHAR,
        rows_affected BIGINT, rows_in BIGINT, example_before VARCHAR, example_after VARCHAR, sample_n BIGINT,
        run_id VARCHAR)""")
    run_ts = time.strftime("%Y-%m-%d %H:%M:%S")
    run = {"run_ts": run_ts, "sample_n": sample_n, "run_id": f"silver-{run_ts}"}
    if sample_n:
        build_sample(con, sample_n, log=log)
    out = [build_table(con, t, run, sample_n, log) for t in (tables or TABLES)]

    # DC-COLL-001: orphan contacts must stay below 1% (only when contact_history was rebuilt in this run)
    if "contact_history" not in (tables or TABLES):
        log(f"  silver done in {time.time() - t0:.1f}s; fix_log run_id={run['run_id']}")
        con.close()
        return out
    o = con.execute("""SELECT count(*) FILTER (WHERE list_contains(dq_flags, 'orphan_case')), count(*)
                       FROM silver.contact_history""").fetchone()
    rate = 100.0 * o[0] / max(o[1], 1)
    verdict = "PASS" if rate < 1 else "FAIL"
    _log(con, run, "contact_history", f"dc_coll_001_orphan_rate_{rate:.2f}pct_{verdict}", o[0], o[1])
    log(f"  DC-COLL-001 orphan contacts: {o[0]:,} of {o[1]:,} = {rate:.2f}% (rule < 1%): {verdict}")
    log(f"  silver done in {time.time() - t0:.1f}s; fix_log run_id={run['run_id']}")
    con.close()
    return out


def fix_log_summary(con, run_id: str | None = None) -> list[tuple]:
    run_id = run_id or con.execute("SELECT max(run_id) FROM silver.fix_log").fetchone()[0]
    return con.execute("""SELECT table_name, rule, rows_affected, rows_in, example_before, example_after
                          FROM silver.fix_log WHERE run_id = ? ORDER BY table_name, rule""", [run_id]).fetchall()


def write_fix_log_report(con, path: str = "reports/silver_fix_log.md") -> str:
    """Markdown summary of the latest full-data run per table (falls back to sample runs if no full run)."""
    from pathlib import Path
    from tabulate import tabulate
    full = con.execute("SELECT count(*) FROM silver.fix_log WHERE sample_n IS NULL").fetchone()[0] > 0
    where = "sample_n IS NULL" if full else "sample_n IS NOT NULL"
    rows = con.execute(f"""
        WITH latest AS (SELECT table_name, max(run_id) AS run_id FROM silver.fix_log WHERE {where} GROUP BY 1)
        SELECT f.table_name, f.rule, f.rows_affected, f.rows_in, f.example_before, f.example_after, f.run_id
        FROM silver.fix_log f JOIN latest l USING (table_name, run_id)
        WHERE f.rows_affected > 0 OR f.rule IN ('exact_duplicate_removed', 'latest_snapshot_per_key',
                                                'cdc_current_version_per_key')
        ORDER BY 1, 2""").fetchall()
    counts = [(t, con.execute(f"SELECT count(*) FROM silver.{t}").fetchone()[0])
              for t in TABLES + [f"{t}_duplicates" for t in TABLES]
              if con.execute("SELECT count(*) FROM duckdb_tables() WHERE schema_name='silver' AND table_name=?",
                             [t]).fetchone()[0]]
    md = [f"# Silver fix log ({'full data' if full else 'SAMPLE run'})", "",
          "Generated by `python run.py silver` from `silver.fix_log` (latest run per table). "
          "Feeds the data quality report.", "", "## Row counts", "",
          tabulate(counts, headers=["silver table", "rows"], tablefmt="github", intfmt=","), "",
          "## Rules applied", "",
          tabulate([(t, r, f"{n:,}", f"{100 * n / max(i, 1):.2f}%", (b or "")[:35], (a or "")[:35])
                    for t, r, n, i, b, a, _ in rows],
                   headers=["table", "rule", "rows", "% of rows in", "example before", "example after"],
                   tablefmt="github"),
          "", "Runs: " + ", ".join(sorted({r[6] for r in rows}))]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(md) + "\n", encoding="utf-8")
    return path
