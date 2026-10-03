# Data quality report
Generated: 2026-10-03 22:46:08

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

| id                                            | scope                           |   records |   failing | rule                                                                                                                    | status   |
|-----------------------------------------------|---------------------------------|-----------|-----------|-------------------------------------------------------------------------------------------------------------------------|----------|
| Q1_customer_golden_coverage                   | c360_customer                   |         0 |         0 | every golden_id in id_xref present in c360_customer                                                                     | pass     |
| Q2_account_golden_coverage                    | c360_account                    | 1,633,394 |         0 | every account.golden_id resolves to a c360_customer                                                                     | pass     |
| Q3_live_account_has_product_and_status        | c360_account                    | 1,071,741 |         0 | live accounts have product_code AND account_status                                                                      | pass     |
| Q4_hardship_supportive_next_action            | c360_case                       |    46,865 |         0 | hardship cases do not schedule harsher treatments (CLAUDE §4.6)                                                         | pass     |
| Q5_cease_contact_customers_no_future_outbound | c360_customer x contact_history |    19,997 |         0 | cease-contact customers have no outbound contact scheduled after as_of                                                  | pass     |
| Q6_primary_phone_e164_valid_for_active_cases  | c360_customer x c360_case       |    83,677 |     1,210 | open cases have a valid NANP phone for the customer (gives Layer 4 something to dial) (observed 1.45%; threshold <= 5%) | pass     |
| Q7_orphan_contacts_rate_lt_1pct_DC_COLL_001   | contact_history                 | 2,560,811 |    25,555 | DC-COLL-001: orphan contact rate under 1% (observed 1.00%)                                                              | pass     |

## 3. Identity resolution summary (from match report)

# Identity resolution report
Snapshot: 2026-10-03 22:22:55
Sample: N=full customers
Probabilistic method: **splink** (splink falls back to rules if training fails)
## Probabilistic matcher vs deterministic truth (CRM pointer + national_id_hash)
- Truth pairs: 18,928
- Predicted (any band): 27,844
- True positives: 18,742
- **Recall**: 0.990 (of known CRM duplicates found)
- **Precision**: 0.673 (floor only: non-truth predictions include real duplicates the CRM did not record, so true precision is higher - needs manual spot-checks)
## Coverage by source
| source      | keys linked / total   | coverage %   | deterministic %   |
|-------------|-----------------------|--------------|-------------------|
| cards       | 584,725/660,000       | 88.6%        | 88.6%             |
| collections | 356,864/367,229       | 97.2%        | 97.2%             |
| crm         | 1,020,000/1,020,000   | 100.0%       | 100.0%            |
| deposits    | 686,725/780,000       | 88.0%        | 88.0%             |
| external    | 514,407/1,000,000     | 51.4%        | 51.4%             |
| loans       | 360,836/404,500       | 89.2%        | 89.2%             |
### Bridge-coverage warnings
- **cards**: deterministic coverage 88.6% - fix the bridge, do not paper over with Splink
- **deposits**: deterministic coverage 88.0% - fix the bridge, do not paper over with Splink
- **external**: deterministic coverage 51.4% - fix the bridge, do not paper over with Splink
- **loans**: deterministic coverage 89.2% - fix the bridge, do not paper over with Splink
