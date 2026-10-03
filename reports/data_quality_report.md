# Data quality report
Generated: 2026-10-03 21:22:02

## 1. Silver cleaning (one row per rule, latest full run)

| table            | issue                                                       |   records affected | share           | how handled                                                                 |
|------------------|-------------------------------------------------------------|--------------------|-----------------|-----------------------------------------------------------------------------|
| agent_notes      | flag:note_placeholder                                       |             51,659 | 6.79% of rows   | see silver.fix_log                                                          |
| agent_notes      | agent_notes NA/N/A/na/- placeholder bodies                  |             51,659 | 6.79% of rows   | set to NULL; original kept in note_placeholder                              |
| card_accounts    | card DOB (DD-MM-YYYY) parsed                                |            660,000 | 100.00% of rows | parsed to DATE                                                              |
| card_accounts    | card_accounts phone comes partially masked by source        |            384,422 | 58.25% of rows  | pattern kept in cardholder_phone_mask                                       |
| card_accounts    | card/loan/deposit rows with snapshot_date before 2026-09-28 |            129,883 | 19.68% of rows  | silver flag stale_snapshot (closed / written-off accounts)                  |
| card_accounts    | card holder phone normalised to +1 E.164                    |            255,981 | 38.78% of rows  | built from raw digits where unmasked                                        |
| card_accounts    | cardholder postal code normalised to A1A 1A1                |            653,336 | 98.99% of rows  | space inserted, O/I -> 0/1 at digit positions                               |
| contact_history  | contact_history exact duplicate rows                        |            127,526 | 4.74% of rows   | deduped; silver.contact_history_duplicates records the kept id              |
| contact_history  | contact_history rows carrying channel from channel_v2       |             31,428 | 1.17% of rows   | silver flag channel_from_v2                                                 |
| contact_history  | contact_history rows with case_id not in collections_cases  |             26,864 | 1.00% of rows   | silver flag orphan_case; see DC-COLL-001 Q7 check                           |
| contact_history  | info:na_kept_as_code_no_answer                              |            228,124 | 8.49% of rows   | see silver.fix_log                                                          |
| contact_history  | contact_history.channel_v2 after REL-0926 release           |             19,463 | 0.72% of rows   | coalesced into one channel column, old column dropped                       |
| customers        | CRM DOB with both DD/MM and MM/DD interpretations           |            128,980 | 12.65% of rows  | both readings kept (dob_parsed + dob_alt)                                   |
| customers        | CRM DOB parsed from mixed formats                           |            405,432 | 39.75% of rows  | ISO date in dob_parsed                                                      |
| customers        | mixed-case emails on CRM                                    |              9,593 | 0.94% of rows   | lower-cased and trimmed                                                     |
| customers        | CRM records marked deleted (cdc_operation='D')              |              2,115 | 0.21% of rows   | silver flag cdc_deleted; still carried, excluded from live surrogate choice |
| customers        | CRM DOB ambiguous day/month                                 |            128,980 | 12.65% of rows  | silver flag dob_ambiguous; both readings kept                               |
| customers        | CRM primary phone fails NANP validation                     |              4,944 | 0.48% of rows   | silver flag phone_invalid; left NULL in e164 column                         |
| customers        | info:na_kept_as_real_first_name                             |                 15 | 0.00% of rows   | see silver.fix_log                                                          |
| customers        | CRM middle_name 'X' placeholder                             |              1,462 | 0.14% of rows   | set to NULL                                                                 |
| customers        | CRM secondary phone normalised to +1 E.164                  |            356,870 | 34.99% of rows  | built from raw digits                                                       |
| customers        | CRM work phone normalised to +1 E.164                       |             60,943 | 5.97% of rows   | built from raw digits                                                       |
| customers        | CRM province_code variants (Ont., B.C., ...)                |             10,689 | 1.05% of rows   | normalised to 2-letter code                                                 |
| deposit_accounts | deposit CIF left-padded to 10 digits                        |            156,837 | 20.11% of rows  | padded in silver.deposit_accounts                                           |
| deposit_accounts | deposit DOB (YYYYMMDD) parsed                               |            764,244 | 97.98% of rows  | parsed to DATE                                                              |
| deposit_accounts | deposits with lost leading zeros detected                   |            156,837 | 20.11% of rows  | silver flag cif_padded; CIF padded                                          |
| deposit_accounts | card/loan/deposit rows with snapshot_date before 2026-09-28 |            158,186 | 20.28% of rows  | silver flag stale_snapshot (closed / written-off accounts)                  |
| deposit_accounts | deposit holder phone normalised to +1 E.164                 |            749,003 | 96.03% of rows  | built from raw digits                                                       |
| external         | DFI-0812 shifted-column bureau rows                         |              9,918 | 0.99% of rows   | 4 inquiry columns rotated back; dfi0812_as_loaded keeps the originals       |
| external         | DFI-0812: hard_12m value was the hard_6m value              |              3,925 | 0.39% of rows   | rotated back                                                                |
| external         | DFI-0812: hard_3m value was the soft_12m value              |              9,918 | 0.99% of rows   | rotated back                                                                |
| external         | DFI-0812: hard_6m value was the hard_3m value               |              3,013 | 0.30% of rows   | rotated back                                                                |
| external         | DFI-0812: soft_12m value was the hard_12m value             |              9,885 | 0.99% of rows   | rotated back                                                                |
| loan_accounts    | loan DOB (YYYY/MM/DD) parsed                                |            400,468 | 99.00% of rows  | parsed to DATE                                                              |
| loan_accounts    | card/loan/deposit rows with snapshot_date before 2026-09-28 |             73,021 | 18.05% of rows  | silver flag stale_snapshot (closed / written-off accounts)                  |
| loan_accounts    | loan borrower phone normalised to +1 E.164                  |            396,287 | 97.97% of rows  | built from raw digits                                                       |

## 2. Gold C360 quality checks

| id                                            | scope                           |   records |   failing | rule                                                                                  | status   |
|-----------------------------------------------|---------------------------------|-----------|-----------|---------------------------------------------------------------------------------------|----------|
| Q1_customer_golden_coverage                   | c360_customer                   |         0 |         0 | every golden_id in id_xref present in c360_customer                                   | pass     |
| Q2_account_golden_coverage                    | c360_account                    |    82,240 |         0 | every account.golden_id resolves to a c360_customer                                   | pass     |
| Q3_live_account_has_product_and_status        | c360_account                    |    53,966 |         0 | live accounts have product_code AND account_status                                    | pass     |
| Q4_hardship_supportive_next_action            | c360_case                       |    46,865 |         0 | hardship cases do not schedule harsher treatments (CLAUDE §4.6)                       | pass     |
| Q5_cease_contact_customers_no_future_outbound | c360_customer x contact_history |       970 |         0 | cease-contact customers have no outbound contact scheduled after as_of                | pass     |
| Q6_primary_phone_e164_valid_for_active_cases  | c360_customer x c360_case       |     4,067 |        70 | open cases have a valid NANP phone for the customer (gives Layer 4 something to dial) | fail     |
| Q7_orphan_contacts_rate_lt_1pct_DC_COLL_001   | contact_history                 | 2,560,811 |    25,555 | DC-COLL-001: orphan contact rate under 1% (observed 1.00%)                            | pass     |

## 3. Identity resolution summary (from match report)

# Identity resolution report
Snapshot: 2026-10-03 21:02:18
Sample: N=50000 (silver.* sample)
Probabilistic method: **splink** (splink falls back to rules if training fails)
## Probabilistic matcher vs deterministic truth (CRM pointer + national_id_hash)
- Truth pairs: 314
- Predicted (any band): 756
- True positives: 313
- **Recall**: 0.997 (of known CRM duplicates found)
- **Precision**: 0.414 (floor only: non-truth predictions include real duplicates the CRM did not record, so true precision is higher - needs manual spot-checks)
> **Reading the numbers.** The only ground truth available on the laptop is pairs the CRM itself marks
> as duplicates (`duplicate_of_crm_id` pointer or shared `national_id_hash`). Splink finds 99.7% of those
> and does not predict any pair that we are *sure* is wrong. The 0.414 "precision" therefore is a floor,
> not a verdict: the gap between recall (0.997) and precision (0.414) is strong evidence that Splink is
> finding real duplicates the CRM never flagged (same person, two CRM records opened months apart with
> no national_id captured on one of them). A fair precision number needs manual review of a spot-check
> set, which is the right job for the steward queue (`silver.steward_queue`).
## Coverage by source
| source      | keys linked / total   | coverage %   | deterministic %   |
|-------------|-----------------------|--------------|-------------------|
| cards       | 29,636/29,636         | 100.0%       | 100.0%            |
| collections | 17,517/17,517         | 100.0%       | 100.0%            |
| crm         | 50,287/50,287         | 100.0%       | 100.0%            |
| deposits    | 34,484/37,482         | 92.0%        | 92.0%             |
| external    | 25,980/28,805         | 90.2%        | 90.2%             |
| loans       | 18,118/18,118         | 100.0%       | 100.0%            |
