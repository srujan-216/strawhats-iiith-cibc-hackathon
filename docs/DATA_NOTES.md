# Data notes: Maple Bank collections release

Checked on 2026-10-03 against the full data (`python run.py register`, then DuckDB queries on `main.*`
and `raw.*`). Release folder: `../maple_data/maple_collections_release/`. Snapshot ("today") = **2026-09-28**.
When this file and the dictionary disagree, this file describes what the data actually contains.

## 1. Loading summary

- All **31 tables** are found by `register`. Row counts match the README exactly (e.g. customers 1,020,000;
  contact_history 2,688,337; loan_instalments 14,832,472; transactions 12,401,924).
- 25 CSV tables are materialised in `warehouse/maple.duckdb`. The 6 Parquet history tables are views over the
  files: Hive-partitioned `year=YYYY/part-NNN.parquet`, which adds `year` and `filename` columns.
- `schema/schema.json` gives each column a physical type. `register` now forces every column declared
  `VARCHAR` to text in `main.*` and prints any column whose loaded type differs from the schema.
  - Before the fix: `call_transcripts.transcript_id`, `contact_history.transcript_id`,
    `voice_samples.transcript_id` and `external.bureau_file_number` loaded as BIGINT.
  - After the fix, 23 differences remain, all harmless: whole-number money columns (e.g. `credit_limit`,
    `annual_fee`, `declared_annual_income`) load as BIGINT where the schema says DOUBLE. DuckDB `/` is float
    division, so arithmetic is unaffected.
- `schema/load_duckdb.sql` is the release's own loader. It drops the `year` partition column.

## 2. Customer keys (five source systems)

There is no shared customer ID. Patterns: `A` = letter, `9` = digit.

| System | Table.column | Format | Rows / distinct | Notes |
|---|---|---|---|---|
| CRM | `customers.crm_customer_id` | `AAA-9999` (e.g. `KAG-8931`) | 1,020,000 / 1,020,000 | one per CRM *record*; a person can have 2 |
| Cards | `card_accounts.src_customer_ref` | `CX9999999` (`AA9999999`) | 660,000 / 550,000 | card-system customer number |
| Lending | `loan_accounts.src_customer_ref` | `B99999999` (`A99999999`) | 404,500 / 340,000 | borrower number |
| Core banking | `deposit_accounts.src_customer_ref` | 10-digit CIF, text | 780,000 / 644,202 | **leading zeros lost in source on 156,837 rows** (142,665 are 8 digits, 14,172 are 7). `lpad(ref,10,'0')` makes 100% of them match `external.bank_subject_ref` |
| Core banking | `external.bank_subject_ref`, `bureau_history.bank_subject_ref` | 10-digit CIF, always 10 chars | 1,000,000 / 1,000,000 | e.g. `0008477619` |
| Collections | `collections_cases.coll_customer_ref` | `AAA-9999` (CRM id copied at case open) | 367,229 / 288,426 | **10,365 cases (2.8%) point to a CRM id that does not exist** |
| Collections | `contact_history.crm_customer_id`, `promises_to_pay.crm_customer_id`, `agent_notes.crm_customer_id` | `AAA-9999` | | contact_history: 26,704 rows have null `crm_customer_id` |

Account IDs, which link to the deterministic bridges `account_monthly_snapshot(account_id, crm_customer_id)`
and `salary_credit_history(deposit_account_id, crm_customer_id)`:
- cards: `C-999999`
- loans: `L-9999999` (personal_loan, auto_loan, mortgage, unsecured_loc)
- deposits: `CHQ-`, `SAV-`, `TFS-`, `USD-` + digits

CRM duplicates:
- `customers.duplicate_of_crm_id` is set on only **5,950** records (the CRM's own pointer, documented as incomplete).
- `national_id_hash` is null on 65,238 records. **18,496 hashes are shared by 2 records (36,992 records)**,
  so the hash finds about 3x more duplicates than the pointer.
- `customers.cdc_operation`: U 916,466 / I 101,419 / **D 2,115** (deleted records are still present;
  silver must apply CDC).

Each account appears once in its account table. The rows are not a history, but not all are on the snapshot
date: card 129,883 / loan 73,021 / deposit 158,186 rows have `snapshot_date` < 2026-09-28. Of the stale card
rows, 128,203 are `closed` and 1,680 are `charged_off`. These are last snapshots of closed accounts, not
missing data.

## 3. NA codes and null conventions

- CSV: empty field = null (DuckDB default `nullstr=''`). Nothing else is treated as null when loading,
  which is deliberate.
- `NA` is a real code: `contact_history.outcome_code = 'NA'` means "No answer" (228,124 rows;
  `code_lookups` row `outcome_code/NA`, `counts_as_rpc=false`). Never turn it into null. pandas users need
  `keep_default_na=False, na_values=[""]`.
- `agent_notes.note_text` holds placeholder notes: `LM` 28,074, `NA` 28,020, `MV` 9,363, `N/A` 7,936,
  `na` 7,897, `-` 7,806. These are text the agent typed, i.e. empty or "left message" notes. Keep them
  as text and flag them as non-informative in features.
- Other code values that look like nulls are real categories:
  - `'none'` in `card_accounts.rewards_program`, `loan_accounts.collateral_type`, `*.insurance_claim_status`,
    `hardship_programs.min_hardship_level`, `metric_definitions.default_filters`
  - `'unknown'` in `contact_history.consent_status_at_time` (26,949) and `amd_result` (304,975)
  - `customers.gender_code` `X`/`U` (protected; do not use)
  - `customers.middle_name = 'X'` 1,462: placeholder, treat as null in name matching
  - `customers.first_name = 'NA'` 15: probably a placeholder
- No numeric sentinels found: the -1/999/9999 checks came back empty. Ranges are sane (age 18–85,
  risk_score 300–850, dpd 0–181, income 9,000–900,000). Missing numbers are real nulls, e.g. income null
  71,428, risk_score null 72,021, card dpd null 52,734.

## 4. Date and timestamp formats

- **Typed CSV columns are ISO and parse cleanly**: dates are `YYYY-MM-DD`, timestamps `YYYY-MM-DD HH:MM:SS`.
  All columns the schema declares DATE (92) or TIMESTAMP (38) loaded as DATE/TIMESTAMP with no errors.
- Timestamps are in the **customer's local time** unless the name ends in `_utc`. Only
  `contact_history.contact_ts_utc` and `agent_notes.note_ts_utc` are UTC. `ops_events` are Eastern Time.
- Mixed or system-specific formats are in the identity columns. These matter for matching:

| Table.column | Format(s) | Count |
|---|---|---|
| `customers.dob_raw` | `YYYY-MM-DD` | 609,542 |
|  | `NN/NN/YYYY`, **both MM/DD and DD/MM** (122,353 have first part >12, 91,531 second part >12; the rest are ambiguous) | 354,791 |
|  | `Mon DD YYYY` | 50,641 |
|  | null | 5,026 |
| `customers.date_of_birth` | DATE (already parsed by CRM) | |
| `card_accounts.cardholder_dob_raw` | `DD-MM-YYYY` (day first: second part never >12) | 660,000 |
| `loan_accounts.borrower_dob_raw` | `YYYY/MM/DD` | 400,468 + 4,032 null |
| `deposit_accounts.holder_dob_raw` | `YYYYMMDD` | 764,244 + 15,756 null |
| `external.subject_dob_reported` | DATE (ISO) | |
| `account_monthly_snapshot.month_end_date` (VARCHAR in Parquet) | `YYYY-MM-DD` | 11,314,540 |
|  | `NN/NN/YYYY`, both DD/MM and MM/DD (month-ends, so the day ≥28 makes it unambiguous) | 837,071 |
|  | `YYYYMMDD` | 418,081 |
| `salary_credit_history.credit_month` | `YYYY-MM` | |
| Other Parquet date columns | typed DATE/TIMESTAMP | |

## 5. Schema drift, CDC and known incidents (`ops_events`)

- **`contact_history.channel` → `channel_v2`** (REL-0926, 2026-09-26 00:00–02:00):
  - 2,656,909 rows have only `channel`
  - 19,463 rows have only `channel_v2`
  - 11,965 have both
  - `channel_v2` appears only from 2026-09-26 08:30 to 2026-09-28 06:56

  Silver must coalesce them (`coalesce(channel_v2, channel)`) and log it.
- INC-0914 (2026-09-14): in-app payments posted a day late and **late fees were charged in error**, about 1,900
  customers (card_statements, collections_cases, contact_history).
- INC-0923 (2026-09-23 08:00 to 09-24 21:00): dialer degraded, call capacity down about 60%. This affects
  contact_history and channel_capacity, so expect a dip in contacts.
- DFI-0812 (2026-08-12): bureau fixed-width file loaded with a **shifted column for some rows**, about 10,000 in
  `external`. Not marked in the data, so we have to find it.
- POL-0301 (2026-03-01): hardship policy v4.2 (reduced payment 50% for 3 months, evidence rule).
- ECO-0715 (from 2026-07-15): Windsor-Essex layoffs lead to more job-loss hardship.
- `contact_history`: 26,864 rows have a `case_id` not in `collections_cases` (1.0%). DC-COLL-001 allows
  orphans < 1%, so this is **just over the limit**.
- `batch_id` exists on every table, e.g. `CRM_20260928_01`, `CRD_20260828_01` for stale snapshots.
- Version columns:
  - `collections_cases.strategy_version` v3.2 / v3.1 / v2.4
  - `model_scores.model_version` v2.3 / v1.2 / v1.1 / v0.9
  - `loan_instalments.schedule_version` 1 or 2 (47,978 re-scheduled)
  - `hardship_programs.version` 2025.1 / 2026.1

## 6. Labels, contract and documents

- **500 note labels**: `labels/agent_notes_labels_public_500.csv`, keyed by `note_id`. Has `label_*` columns
  (hardship, delay reason, PTP amount/date/intent, dispute, complaint, vulnerability, cease request,
  insolvency, sentiment, next step, ...) plus labeller id, confidence and `inter_annotator_agreement`.
- **500 transcript labels**: `labels/call_transcripts_labels_public_500.csv`, keyed by `transcript_id`. Has the
  same `label_*` columns plus 10 QA checklist items (`qa01`…`qa10` with evidence second and text),
  `qa_total_score`, `summary_gold_json` and `policy_sections_relevant`.
- `labels/` is registered only as the `hidden` schema (`hidden.*`). Runtime code and Layer 2 must never
  read it.
- **DC-COLL-001** (the data contract to base ours on):
  `files/docs/data_contracts/DC-COLL-001_v1.0_EN.md`; also listed in `reference_documents` (doc_type
  `data_contract`, effective 2026-06-01). It covers `contact_history`:
  - owner Collections Data Office, daily refresh 05:00 ET
  - rules: `contact_id` unique, `contact_ts_utc` not null, `case_id` in collections_cases (orphans < 1%),
    channel in code list
  - allowed uses: ops, analytics, model training; not marketing
- **Policy documents** (`files/docs/**`, catalogue in `reference_documents`, 19 rows):
  - Superseded versions to exclude from RAG: `POL-COLL-004-V4.1` (→ POL-COLL-004 v4.2) and
    `SCR-MID-STD-EN-V1.0` (→ SCR-MID-STD-EN v2.0). Use `superseded_by IS NULL` for current versions.
  - French copies: `-FR` docs and `REG-SUM-001-QC`.
- Transcript bodies: `files/transcripts/YYYY/MM/<transcript_id>.json`, referenced by
  `call_transcripts.file_path` (relative to `files/`). The `turn.*`, `turns` and `turn_count` columns in the
  dictionary are only in the JSON files, not in the CSV (29 cols, not 39).

## 7. Benchmark files

| File | Columns | Notes |
|---|---|---|
| `data/benchmark_questions.csv` (35 rows) | `question_id, question_text, difficulty, metric_id, as_of_date, tolerance, split` | **`split` column marks dev (21) / test (14)**. ⚠ `metric_id` (set on 15) and `tolerance` (19) are in this runtime table but are banned at runtime (CLAUDE.md rule 2). Layer 2 must only read `question_id, question_text, as_of_date` |
| `labels/benchmark_dev_answers.csv` (21 rows) | `question_id, gold_answer, gold_sql_reference, gold_sources, trap_notes` | dev gold only; read only by `src/layer2/evaluate.py` |
| `labels/benchmark_answers_template.csv` | `question_id, answer, sql_or_sources, refused` | submission format, one row per question |

Extra questions come at 19:00 IST on 4 Oct. Some questions should be refused.

## 8. Where the dictionary and the data disagree

| Topic | Dictionary says | Data / README says |
|---|---|---|
| `deposit_accounts` columns | 143 | **145**: `overdraft_dpd`, `overdraft_dpd_bucket` added (README mentions it; dictionary does not) |
| `call_transcripts` columns | 39 | **29** in CSV: the 10 `turn*` fields are only in the JSON files |
| collections_cases rows | ~340K | 367,229 |
| contact_history rows | ~2.5M | 2,688,337 |
| promises_to_pay rows | ~400K | **238,815** |
| agent_notes rows | ~1.5M | **760,594** |
| loan_instalments rows | ~20M | 14,832,472 |
| transactions rows | ~10M | 12,401,924 |
| bureau_history rows | ~5M | 4,679,562 |
| card / loan / deposit "one row per" | account per snapshot_date | one row per account (last snapshot; closed accounts keep an older `snapshot_date`) |
| `transcript_id`, `bureau_file_number` | string | all digits, so loaders guess integer; we force text |
| `account_monthly_snapshot.month_end_date` | date | VARCHAR in Parquet with 3 formats (section 4) |
| `customers.duplicate_of_crm_id` | duplicate pointer | covers 5,950 records; `national_id_hash` shows 18,496 shared hashes |
| `contact_history.channel` | one column | split into `channel` / `channel_v2` since REL-0926 |
| `account_monthly_snapshot` | month-end history | quarter-end only (Dec 2023 to Jun 2026) plus post-write-off rows (README) |
