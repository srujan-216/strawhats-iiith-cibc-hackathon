# Handoff: silver layer (S1), for Varshith

Status 2026-10-03: `python run.py silver` has run on the **full data on Srujan's laptop**, all 9 tables.
Results are in `reports/silver_fix_log.md`. Rules and evidence are in `src/layer1/silver.py` and `docs/DATA_NOTES.md`.

## What you need to do on the GPU workstation

```bash
git checkout srujan/silver        # or main once the PR is merged
python run.py register            # ~10 min; builds warehouse/maple.duckdb from the release
python run.py silver              # ~12 min on the laptop with 2 GB / 4 threads; faster with more memory
```

- **Memory:** raise the limits in `config.yaml` → `silver.memory_limit` / `silver.threads` (e.g. `16GB` / `16`).
  On the laptop a 4 GB run was killed for low system memory, so the laptop uses 2 GB and spills to
  `warehouse/tmp/`.
- **Partial reruns:** `python run.py silver --tables contact_history external`. Each run appends to
  `silver.fix_log` with its own `run_id`; the report uses the latest full run per table.
- **Expected numbers** (check that yours match):

| table | rows out | key rule counts |
|---|---:|---|
| customers | 1,020,000 | 128,980 ambiguous DOB (`dob_alt` kept); 2,115 `cdc_deleted` (`is_deleted`); 4,944 invalid primary phones; 10,689 provinces standardised |
| card_accounts | 660,000 | 384,422 masked phones (`cardholder_phone_mask`); 129,883 stale (closed) snapshots |
| loan_accounts | 404,500 | 73,021 stale snapshots |
| deposit_accounts | 780,000 | **156,837 CIFs left-padded to 10 digits** |
| collections_cases | 367,229 | (no changes) |
| contact_history | **2,560,811** | **127,526 exact duplicates removed** (listed in `silver.contact_history_duplicates`); 31,428 `channel_from_v2`; 26,864 `orphan_case` before dedupe, 25,555 after = 0.998% (DC-COLL-001 < 1%: pass, barely) |
| promises_to_pay | 238,815 | (no changes) |
| agent_notes | 760,594 | 51,659 placeholder notes (`NA`, `N/A`, `na`, `-`) set to NULL; original kept in `note_placeholder` |
| external | 1,000,000 | **9,918 DFI-0812 rows repaired** (`repaired_DFI0812`, original values in `dfi0812_as_loaded`) |

## Using silver in Layer 3/4

- **Keys:** `silver.customers.crm_customer_id`, `silver.collections_cases.case_id`. Deposit CIFs are now
  10 digits and join to `external.bank_subject_ref`.
- **Rows to exclude or treat with care:**
  - `customers.is_deleted = true`: exclude from C360.
  - `dq_flags` contains `orphan_case`: no case to join to.
  - `dq_flags` contains `duplicate_referenced`: kept only because a note points to it. None in the current data.
- **`dq_flags`** is a `VARCHAR[]`; test with `list_contains(dq_flags, 'repaired_DFI0812')`.
- **Contact channel:** `contact_history.channel` already merges `channel_v2`, so don't look for `channel_v2`.
- **Outcome codes:** `contact_history.outcome_code = 'NA'` means **no answer**. It is not a null.
- **Protected attributes:** silver keeps all columns, including protected ones such as `gender_code` and
  `age`. The feature code must drop them (CLAUDE.md §2).
