# Source profile

| table | rows | columns |
|---|---:|---:|
| account_monthly_snapshot | 12,569,692 | 17 |
| agent_notes | 760,594 | 26 |
| agent_shifts | 15,317 | 15 |
| agents | 1,000 | 30 |
| benchmark_questions | 35 | 7 |
| bureau_history | 4,679,562 | 11 |
| call_transcripts | 25,000 | 29 |
| card_accounts | 660,000 | 148 |
| card_statements | 7,531,283 | 27 |
| case_assignment_history | 423,830 | 23 |
| channel_capacity | 287 | 11 |
| code_lookups | 113 | 7 |
| collections_cases | 367,229 | 132 |
| contact_history | 2,688,337 | 128 |
| customers | 1,020,000 | 148 |
| deposit_accounts | 780,000 | 145 |
| external | 1,000,000 | 122 |
| geo_reference | 656 | 15 |
| hardship_programs | 18 | 21 |
| loan_accounts | 404,500 | 135 |
| loan_instalments | 14,832,472 | 20 |
| metric_definitions | 15 | 14 |
| model_scores | 1,718,841 | 33 |
| offers | 40,767 | 19 |
| ops_events | 6 | 10 |
| promises_to_pay | 238,815 | 29 |
| qa_checklist | 10 | 10 |
| reference_documents | 19 | 17 |
| salary_credit_history | 6,000,000 | 12 |
| transactions | 12,401,924 | 26 |
| voice_samples | 2,000 | 34 |

## account_monthly_snapshot (12,569,692 rows)

| column_name              | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:-------------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| account_id               | VARCHAR       |              0    |          179729 | C-100017                       | USD-995148                     |
| crm_customer_id          | VARCHAR       |              0    |          166461 | AAA-1427                       | ZOZ-8896                       |
| month_end_date           | VARCHAR       |              0    |              47 | 03/31/2024                     | 31/12/2025                     |
| product_type             | VARCHAR       |              0    |               9 | auto_loan                      | usd_account                    |
| account_status           | VARCHAR       |              0    |               3 | active                         | delinquent                     |
| balance                  | DOUBLE        |              0    |          171206 | -5064.93                       | 1487006.58                     |
| limit_or_original_amount | DOUBLE        |             43.41 |            1401 | 500.0                          | 1500000.0                      |
| minimum_due              | DOUBLE        |             43.16 |           34031 | 0.0                            | 8541.7                         |
| payment_made             | DOUBLE        |             43.16 |           30824 | 0.0                            | 11996.7                        |
| dpd                      | BIGINT        |              7.95 |             666 | 0                              | 3317                           |
| dpd_bucket               | VARCHAR       |              0    |               9 | 1-30                           | current                        |
| overlimit_flag           | BOOLEAN       |              0    |               2 | false                          | true                           |
| write_off_flag           | BOOLEAN       |              0    |               2 | false                          | true                           |
| salary_credit_amount     | DOUBLE        |             72.22 |           55214 | 486.19                         | 52502.82                       |
| batch_id                 | VARCHAR       |              0    |              12 | AMS_202312                     | AMS_202606                     |
| filename                 | VARCHAR       |              0    |              95 | D:\iiith\maple_data\maple_coll | D:\iiith\maple_data\maple_coll |
| year                     | BIGINT        |              0    |               4 | 2023                           | 2026                           |

## agent_notes (760,594 rows)

| column_name          | column_type   |   null_percentage |   approx_unique | min                         | max                          |
|:---------------------|:--------------|------------------:|----------------:|:----------------------------|:-----------------------------|
| note_id              | VARCHAR       |              0    |          181391 | N-0000002                   | N-9537268                    |
| contact_id           | VARCHAR       |              1.93 |          212029 | CT-0000017                  | CT-9626678                   |
| case_id              | VARCHAR       |              0    |          124524 | CS-2016-102781              | CS-2026-999984               |
| crm_customer_id      | VARCHAR       |              0    |          102970 | AAA-2567                    | ZOZ-9840                     |
| account_id           | VARCHAR       |             29.88 |           87201 | C-100026                    | L-9999436                    |
| agent_id             | VARCHAR       |             10.27 |             848 | AG-1003                     | AG-9999                      |
| note_ts              | TIMESTAMP     |              0    |          212345 | 2016-10-10 14:41:18         | 2026-09-27 22:37:28          |
| note_ts_utc          | TIMESTAMP     |              0    |          183280 | 2016-10-10 18:41:18         | 2026-09-28 04:04:59          |
| note_type            | VARCHAR       |              0    |               7 | call_note                   | system_note                  |
| note_source          | VARCHAR       |              0    |               4 | auto_system                 | typed                        |
| template_id          | VARCHAR       |             90.69 |              15 | TPL-CALL-01                 | TPL-PAYM-04                  |
| note_text            | VARCHAR       |              3.09 |           83535 | -                           | wrong number, skip trace req |
| note_language        | VARCHAR       |              0    |               3 | EN                          | mixed                        |
| note_length_chars    | BIGINT        |              0    |             255 | 0                           | 255                          |
| word_count           | BIGINT        |              0    |              45 | 0                           | 47                           |
| abbreviation_count   | BIGINT        |              0    |               7 | 0                           | 6                            |
| contains_amount_flag | BOOLEAN       |              0    |               2 | false                       | true                         |
| contains_date_flag   | BOOLEAN       |              0    |               2 | false                       | true                         |
| edited_flag          | BOOLEAN       |              0    |               2 | false                       | true                         |
| edit_count           | BIGINT        |              0    |               4 | 0                           | 3                            |
| last_edited_ts       | TIMESTAMP     |             95    |            7303 | 2016-10-17 02:53:24         | 2026-09-28 15:45:15          |
| redaction_status     | VARCHAR       |              0    |               3 | auto_redacted               | none                         |
| retention_until      | DATE          |              0    |            4310 | 2023-10-11                  | 2033-09-27                   |
| src_system           | VARCHAR       |              0    |               1 | CRM                         | CRM                          |
| batch_id             | VARCHAR       |              0    |               1 | NOTES_20260928              | NOTES_20260928               |
| file_path            | VARCHAR       |              0    |          241964 | notes/2016/10/N-0500008.txt | notes/2026/09/N-9537268.txt  |

## agent_shifts (15,317 rows)

| column_name            | column_type   |   null_percentage |   approx_unique | min              | max              |
|:-----------------------|:--------------|------------------:|----------------:|:-----------------|:-----------------|
| shift_id               | VARCHAR       |              0    |           16576 | SH-20260914-1009 | SH-20261011-9564 |
| agent_id               | VARCHAR       |              0    |             887 | AG-1003          | AG-9999          |
| shift_date             | DATE          |              0    |              24 | 2026-09-14       | 2026-10-11       |
| site_time_zone         | VARCHAR       |              0    |               3 | America/Edmonton | America/Toronto  |
| start_local            | VARCHAR       |              0    |               3 | 08:00            | 12:00            |
| end_local              | VARCHAR       |              0    |               4 | 16:30            | 20:00            |
| break_minutes          | BIGINT        |              0    |               1 | 60               | 60               |
| scheduled_minutes      | BIGINT        |              0    |               2 | 420              | 480              |
| worked_minutes         | BIGINT        |             47.78 |              97 | 0                | 510              |
| absence_flag           | BOOLEAN       |              0    |               2 | false            | true             |
| absence_reason         | VARCHAR       |             94.56 |               4 | other            | vacation         |
| queue_assignment       | VARCHAR       |              0    |               5 | early_stage      | recoveries       |
| outbound_call_capacity | BIGINT        |              0    |               3 | 54               | 90               |
| evening_slot_capacity  | BIGINT        |              0    |               6 | 3                | 30               |
| overtime_flag          | BOOLEAN       |              0    |               2 | false            | true             |

## agents (1,000 rows)

| column_name                   | column_type   |   null_percentage |   approx_unique | min          | max        |
|:------------------------------|:--------------|------------------:|----------------:|:-------------|:-----------|
| agent_id                      | VARCHAR       |                 0 |            1113 | AG-1003      | AG-9999    |
| agent_display_name            | VARCHAR       |                 0 |             920 | A. Abboud    | É. Séguin  |
| site                          | VARCHAR       |                 0 |               6 | Calgary      | vendor     |
| team_id                       | VARCHAR       |                 0 |              84 | CGY-EARLY-1  | WIN-REC-3  |
| team_lead_id                  | VARCHAR       |                 0 |              72 | AG-1062      | AG-9999    |
| role                          | VARCHAR       |                 0 |               5 | agent        | team_lead  |
| employment_type               | VARCHAR       |                 0 |               2 | employee     | vendor     |
| hire_date                     | DATE          |                 0 |             737 | 2010-01-04   | 2026-08-10 |
| tenure_months                 | BIGINT        |                 0 |             872 | 139263       | 17368105   |
| languages                     | VARCHAR       |                 0 |               6 | ["EN", "FR"] | ["FR"]     |
| skill_early_stage             | BIGINT        |                 0 |               5 | 1            | 5          |
| skill_mid_stage               | BIGINT        |                 0 |               5 | 1            | 5          |
| skill_late_stage              | BIGINT        |                 0 |               5 | 1            | 5          |
| skill_hardship                | BIGINT        |                 0 |               5 | 1            | 5          |
| skill_disputes                | BIGINT        |                 0 |               5 | 1            | 5          |
| skill_auto_loans              | BIGINT        |                 0 |               5 | 1            | 5          |
| vulnerable_customer_certified | BOOLEAN       |                 0 |               2 | false        | true       |
| shift_pattern                 | VARCHAR       |                 0 |               4 | day          | weekend    |
| fte                           | DOUBLE        |                 0 |               3 | 0.6          | 1.0        |
| max_concurrent_cases          | BIGINT        |                 0 |              47 | 150          | 200        |
| current_case_load             | BIGINT        |                 0 |             210 | 0            | 300        |
| rpc_rate_90d                  | DOUBLE        |                 0 |             618 | 0.0          | 1.0        |
| ptp_rate_90d                  | DOUBLE        |                 0 |             501 | 0.0          | 1.0        |
| ptp_kept_rate_90d             | DOUBLE        |                 0 |             534 | 0.0          | 0.7021     |
| cure_rate_90d                 | DOUBLE        |                 0 |             569 | 0.0          | 0.3608     |
| avg_handle_time_sec           | BIGINT        |                 0 |             239 | 229          | 603        |
| qa_score_avg_90d              | DOUBLE        |                 0 |             458 | 66.0         | 100.0      |
| complaints_90d                | BIGINT        |                 0 |              24 | 0            | 22         |
| coaching_flag                 | BOOLEAN       |                 0 |               2 | false        | true       |
| status                        | VARCHAR       |                 0 |               3 | active       | terminated |

## benchmark_questions (35 rows)

| column_name   | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:--------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| question_id   | VARCHAR       |              0    |              43 | BQ-001                         | BQ-035                         |
| question_text | VARCHAR       |              0    |              27 | A customer says their hours we | Why did outbound call volume d |
| difficulty    | VARCHAR       |              0    |               3 | easy                           | medium                         |
| metric_id     | VARCHAR       |             57.14 |              12 | average_dpd                    | write_off_rate                 |
| as_of_date    | DATE          |              0    |               1 | 2026-09-28                     | 2026-09-28                     |
| tolerance     | VARCHAR       |             45.71 |               7 | direction of effect            | ±1 CAD                         |
| split         | VARCHAR       |              0    |               2 | dev                            | test                           |

## bureau_history (4,679,562 rows)

| column_name             | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:------------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| bank_subject_ref        | VARCHAR       |              0    |          201966 | 0001000396                     | 0099999417                     |
| pull_date               | DATE          |              0    |               6 | 2023-10-15                     | 2026-04-15                     |
| hit_status              | VARCHAR       |              0    |               2 | hit                            | thin_file                      |
| risk_score              | BIGINT        |              5.26 |             514 | 315                            | 850                            |
| risk_score_model        | VARCHAR       |              0    |               2 | RS-2.4                         | RS-3.0                         |
| revolving_utilisation   | DOUBLE        |              0    |            9064 | 0.0008                         | 1.056                          |
| delinquent_trades_count | BIGINT        |              0    |               4 | 0                              | 3                              |
| inquiries_hard_6m       | BIGINT        |              0    |              10 | 0                              | 8                              |
| stale_score_flag        | BOOLEAN       |              0    |               2 | false                          | true                           |
| filename                | VARCHAR       |              0    |              81 | D:\iiith\maple_data\maple_coll | D:\iiith\maple_data\maple_coll |
| year                    | BIGINT        |              0    |               4 | 2023                           | 2026                           |

## call_transcripts (25,000 rows)

| column_name            | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:-----------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| transcript_id          | VARCHAR       |                 0 |           20674 | 10000                          | 9511249                        |
| contact_id             | VARCHAR       |                 0 |           26304 | CT-0003960                     | CT-9626626                     |
| call_recording_id      | VARCHAR       |                 0 |           22417 | REC-10000                      | REC-9511249                    |
| voice_sample_id        | VARCHAR       |                92 |            2125 | VS-10000                       | VS-9511247                     |
| case_id                | VARCHAR       |                 0 |           25756 | CS-2016-187819                 | CS-2026-999969                 |
| crm_customer_id        | VARCHAR       |                 0 |           22724 | AAA-3448                       | ZOZ-7954                       |
| agent_id               | VARCHAR       |                 0 |            1060 | AG-1003                        | AG-9999                        |
| call_start_ts          | TIMESTAMP     |                 0 |           21232 | 2016-11-24 12:53:32            | 2026-09-27 16:59:55            |
| call_end_ts            | TIMESTAMP     |                 0 |           20525 | 2016-11-24 12:53:48            | 2026-09-27 17:02:23            |
| duration_sec           | BIGINT        |                 0 |             180 | 12                             | 220                            |
| direction              | VARCHAR       |                 0 |               2 | inbound                        | outbound                       |
| language               | VARCHAR       |                 0 |               2 | en-CA                          | fr-CA                          |
| code_switch_flag       | BOOLEAN       |                 0 |               2 | false                          | true                           |
| asr_engine             | VARCHAR       |                 0 |               1 | asr-telephony                  | asr-telephony                  |
| asr_model_version      | VARCHAR       |                 0 |               1 | v5.1                           | v5.1                           |
| asr_confidence_avg     | DOUBLE        |                 0 |             321 | 0.641                          | 0.969                          |
| wer_estimate           | DOUBLE        |                 0 |             161 | 0.05                           | 0.25                           |
| diarization_confidence | DOUBLE        |                 0 |             135 | 0.85                           | 0.98                           |
| speaker_count          | BIGINT        |                 0 |               3 | 1                              | 3                              |
| customer_talk_ratio    | DOUBLE        |                 0 |             201 | 0.0                            | 0.326                          |
| agent_talk_ratio       | DOUBLE        |                 0 |             569 | 0.244                          | 0.75                           |
| silence_ratio          | DOUBLE        |                 0 |             653 | 0.104                          | 0.657                          |
| overtalk_count         | BIGINT        |                 0 |              14 | 0                              | 12                             |
| hold_count             | BIGINT        |                 0 |               2 | 0                              | 1                              |
| pci_redaction_applied  | BOOLEAN       |                 0 |               1 | true                           | true                           |
| pii_redaction_applied  | BOOLEAN       |                 0 |               1 | true                           | true                           |
| src_system             | VARCHAR       |                 0 |               1 | SPEECH                         | SPEECH                         |
| batch_id               | VARCHAR       |                 0 |               1 | ST_20260928                    | ST_20260928                    |
| file_path              | VARCHAR       |                 0 |           25552 | transcripts/2016/11/7510917.js | transcripts/2026/09/9511249.js |

## card_accounts (660,000 rows)

| column_name                       | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:----------------------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| card_account_id                   | VARCHAR       |              0    |          258353 | C-100000                       | C-999987                       |
| snapshot_date                     | DATE          |              0    |            3370 | 2017-04-05                     | 2026-09-28                     |
| snapshot_type                     | VARCHAR       |              0    |               1 | daily                          | month_end                      |
| card_number_masked                | VARCHAR       |              0    |           54050 | 4510 •••• •••• 1000            | 5410 •••• •••• 9999            |
| src_customer_ref                  | VARCHAR       |              0    |          170905 | CX0000045                      | CX9999951                      |
| cardholder_name_raw               | VARCHAR       |              0    |          134131 | A. ABBOTT                      | ZUNIGA/SHELLEY                 |
| cardholder_dob_raw                | VARCHAR       |              0    |           25477 | 01-01-1941                     | 31-12-2007                     |
| cardholder_phone_raw              | VARCHAR       |              2.99 |          204014 | 2042000379                     | 905999xxx93                    |
| cardholder_postal_raw             | VARCHAR       |              1    |          134656 | A0B0A9                         | Y1A9W6                         |
| product_code                      | VARCHAR       |              0    |               7 | CBV-CLASSIC                    | WEM-ELITE                      |
| card_network                      | VARCHAR       |              0    |               2 | MASTERCARD                     | VISA                           |
| card_tier                         | VARCHAR       |              0    |               4 | classic                        | world_elite                    |
| secured_card_flag                 | BOOLEAN       |              0    |               2 | false                          | true                           |
| security_deposit_amount           | BIGINT        |             92.16 |               4 | 500                            | 2000                           |
| open_date                         | DATE          |              0    |            8860 | 1995-01-27                     | 2026-07-30                     |
| months_on_book                    | BIGINT        |              0    |             403 | 1                              | 380                            |
| account_status                    | VARCHAR       |              0    |               4 | active                         | closed                         |
| block_code                        | VARCHAR       |             93.88 |               4 | A                              | Z                              |
| block_reason_text                 | VARCHAR       |             93.88 |               5 | BKRPT                          | LOST/STOLEN                    |
| block_date                        | DATE          |             93.88 |             147 | 2026-05-31                     | 2026-09-28                     |
| credit_limit                      | BIGINT        |              0    |              80 | 500                            | 50000                          |
| previous_credit_limit             | BIGINT        |             70.06 |              96 | 500                            | 74500                          |
| limit_change_date                 | DATE          |             70.06 |            4101 | 2014-11-19                     | 2026-10-28                     |
| limit_change_reason               | VARCHAR       |             70.06 |               3 | CLD                            | customer_request               |
| cash_advance_limit                | BIGINT        |              0    |             111 | 150                            | 15000                          |
| current_balance                   | DOUBLE        |              0    |          113018 | -138.9                         | 51699.08                       |
| statement_balance                 | DOUBLE        |              0    |          113753 | -964.93                        | 51699.08                       |
| available_credit                  | DOUBLE        |              0    |          139306 | -2549.37                       | 50000.0                        |
| utilisation                       | DOUBLE        |              0    |           10861 | -0.0799                        | 1.3758                         |
| purchase_balance                  | DOUBLE        |              0    |          114488 | 0.0                            | 51699.08                       |
| cash_advance_balance              | BIGINT        |              0    |             385 | 0                              | 9590                           |
| balance_transfer_balance          | DOUBLE        |              0    |            6519 | 0.0                            | 22917.0                        |
| promo_balance                     | DOUBLE        |              0    |           11964 | 0.0                            | 30703.34                       |
| promo_rate                        | DOUBLE        |             93.08 |               4 | 0.0                            | 0.0399                         |
| promo_expiry_date                 | DATE          |             93.08 |             695 | 2017-06-18                     | 2027-07-25                     |
| purchase_apr                      | DOUBLE        |              0    |               5 | 0.1299                         | 0.2299                         |
| cash_apr                          | DOUBLE        |              0    |               3 | 0.1299                         | 0.2499                         |
| penalty_rate_flag                 | BOOLEAN       |              0    |               2 | false                          | true                           |
| annual_fee                        | BIGINT        |              0    |               4 | 0                              | 139                            |
| statement_date                    | DATE          |              0    |            3363 | 2017-03-08                     | 2026-09-28                     |
| statement_cycle_day               | BIGINT        |              0    |              27 | 1                              | 31                             |
| payment_due_date                  | DATE          |              0    |            3270 | 2017-03-29                     | 2026-10-19                     |
| minimum_payment_due               | DOUBLE        |              0    |           19453 | 0.0                            | 9491.11                        |
| min_payment_formula_code          | VARCHAR       |              0    |               1 | MP03                           | MP03                           |
| last_payment_date                 | DATE          |              0.11 |            3431 | 2016-11-14                     | 2026-09-28                     |
| last_payment_amount               | DOUBLE        |              0.11 |           95622 | 1.11                           | 35331.29                       |
| last_payment_channel              | VARCHAR       |              0.11 |               5 | app                            | pad                            |
| payments_mtd                      | DOUBLE        |              0    |           32391 | 0.0                            | 19680.04                       |
| purchases_mtd                     | DOUBLE        |              0    |           35792 | 0.0                            | 12256.74                       |
| cash_advances_mtd                 | BIGINT        |              0    |               1 | 0                              | 0                              |
| interest_charged_mtd              | DOUBLE        |              0    |            7719 | 0.0                            | 799.39                         |
| fees_charged_mtd                  | BIGINT        |              0    |               1 | 0                              | 0                              |
| overlimit_fee_mtd                 | BIGINT        |              0    |               1 | 0                              | 0                              |
| nsf_payment_fee_mtd               | BIGINT        |              0    |               4 | 0                              | 45                             |
| overlimit_flag                    | BOOLEAN       |              0    |               2 | false                          | true                           |
| overlimit_amount                  | DOUBLE        |              0    |             734 | 0.0                            | 2549.37                        |
| past_due_amount                   | DOUBLE        |              0    |           13205 | 0.0                            | 8041.49                        |
| cycles_delinquent                 | BIGINT        |              0    |               9 | 0                              | 7                              |
| dpd                               | BIGINT        |              7.98 |             191 | 0                              | 181                            |
| dpd_bucket                        | VARCHAR       |              0    |               9 | 1-30                           | current                        |
| delinquency_start_date            | DATE          |             93.03 |             598 | 2016-12-07                     | 2026-09-27                     |
| worst_dpd_12m                     | BIGINT        |              0    |             207 | 0                              | 181                            |
| times_30dpd_12m                   | BIGINT        |              0    |               9 | 0                              | 7                              |
| times_60dpd_12m                   | BIGINT        |              0    |               6 | 0                              | 5                              |
| times_90dpd_12m                   | BIGINT        |              0    |               5 | 0                              | 4                              |
| payment_history_24m               | VARCHAR       |              0    |             999 | 000000000000000000000000       | 65321000000XXXXXXXXXXXXX       |
| chargeoff_flag                    | BOOLEAN       |              0    |               2 | false                          | true                           |
| chargeoff_date                    | DATE          |             99.75 |             532 | 2017-06-06                     | 2026-09-19                     |
| chargeoff_amount                  | DOUBLE        |             99.74 |             478 | 420.01                         | 49228.7                        |
| recovery_amount_to_date           | DOUBLE        |             99.74 |             236 | 0.0                            | 20657.51                       |
| autopay_enrolled                  | BOOLEAN       |              0    |               2 | false                          | true                           |
| autopay_type                      | VARCHAR       |             75.12 |               3 | fixed                          | minimum                        |
| autopay_source_account            | VARCHAR       |             75.12 |           12566 | CHQ-100006                     | EXTERNAL                       |
| autopay_failed_count_90d          | BIGINT        |              0    |               4 | 0                              | 3                              |
| rewards_program                   | VARCHAR       |              0    |               3 | cash_back                      | travel_points                  |
| rewards_points_balance            | BIGINT        |              0    |           42260 | 0                              | 119999                         |
| authorized_user_count             | BIGINT        |              0    |               4 | 0                              | 3                              |
| fraud_block_flag                  | BOOLEAN       |              0    |               2 | false                          | true                           |
| dispute_open_flag                 | BOOLEAN       |              0    |               2 | false                          | true                           |
| dispute_amount                    | DOUBLE        |             98.26 |            2849 | 8.46                           | 1858.88                        |
| balance_protection_insurance_flag | BOOLEAN       |              0    |               2 | false                          | true                           |
| insurance_claim_status            | VARCHAR       |             94.97 |               4 | approved                       | submitted                      |
| hardship_program_flag             | BOOLEAN       |              0    |               2 | false                          | true                           |
| hardship_program_type             | VARCHAR       |             99.38 |               5 | debt_management_plan           | skip_payment                   |
| hardship_start_date               | DATE          |             99.38 |             264 | 2023-01-03                     | 2026-09-28                     |
| hardship_end_date                 | DATE          |             99.38 |             396 | 2026-09-29                     | 2030-09-07                     |
| reage_flag                        | BOOLEAN       |              0    |               2 | false                          | true                           |
| reage_date                        | DATE          |             99.53 |             530 | 2016-10-01                     | 2026-09-13                     |
| instalment_plan_flag              | BOOLEAN       |              0    |               2 | false                          | true                           |
| instalment_plan_balance           | DOUBLE        |             94.03 |            8041 | 0.0                            | 17828.66                       |
| last_auth_decline_date            | DATE          |             93.78 |             166 | 2017-05-28                     | 2026-09-28                     |
| auth_declines_30d                 | BIGINT        |              0    |              11 | 0                              | 9                              |
| stmt_balance_m01                  | DOUBLE        |              0.01 |          113753 | -964.93                        | 51699.08                       |
| stmt_balance_m02                  | DOUBLE        |              0.62 |          120028 | 14.74                          | 50851.97                       |
| stmt_balance_m03                  | DOUBLE        |              2.99 |          123788 | 12.12                          | 50018.74                       |
| stmt_balance_m04                  | DOUBLE        |              5.4  |          120154 | 12.55                          | 47290.53                       |
| stmt_balance_m05                  | DOUBLE        |              7.93 |          127031 | 9.1                            | 45852.37                       |
| stmt_balance_m06                  | DOUBLE        |             10.49 |          111912 | 10.27                          | 45101.06                       |
| stmt_balance_m07                  | DOUBLE        |             12.88 |          122802 | 9.31                           | 40315.04                       |
| stmt_balance_m08                  | DOUBLE        |             14.95 |          106258 | 8.36                           | 36384.97                       |
| stmt_balance_m09                  | DOUBLE        |             17.03 |          103909 | 7.84                           | 33204.98                       |
| stmt_balance_m10                  | DOUBLE        |             18.9  |           97820 | 7.49                           | 29353.22                       |
| stmt_balance_m11                  | DOUBLE        |             20.66 |          107725 | 5.62                           | 26994.27                       |
| stmt_balance_m12                  | DOUBLE        |             22.4  |          120378 | 3.55                           | 26183.51                       |
| payment_amount_m01                | DOUBLE        |              0    |           98230 | 0.0                            | 26715.81                       |
| payment_amount_m02                | DOUBLE        |              0.61 |           79130 | 0.0                            | 27354.25                       |
| payment_amount_m03                | DOUBLE        |              2.98 |           85630 | 0.0                            | 35331.29                       |
| payment_amount_m04                | DOUBLE        |              5.39 |           93035 | 0.0                            | 32592.91                       |
| payment_amount_m05                | DOUBLE        |              7.92 |           78896 | 0.0                            | 28242.33                       |
| payment_amount_m06                | DOUBLE        |             10.48 |           74211 | 0.0                            | 37388.06                       |
| payment_amount_m07                | DOUBLE        |             12.87 |           81283 | 0.0                            | 34223.16                       |
| payment_amount_m08                | DOUBLE        |             14.94 |           72030 | 0.0                            | 31075.47                       |
| payment_amount_m09                | DOUBLE        |             17.02 |           69366 | 0.0                            | 27193.79                       |
| payment_amount_m10                | DOUBLE        |             18.89 |           69846 | 0.0                            | 23251.19                       |
| payment_amount_m11                | DOUBLE        |             20.65 |           91659 | 0.0                            | 22466.65                       |
| payment_amount_m12                | DOUBLE        |             22.39 |           77228 | 0.0                            | 23527.27                       |
| dpd_m01                           | BIGINT        |              0    |             207 | 0                              | 180                            |
| dpd_m02                           | BIGINT        |              0    |             159 | 0                              | 151                            |
| dpd_m03                           | BIGINT        |              2.06 |             121 | 0                              | 120                            |
| dpd_m04                           | BIGINT        |              4.51 |             105 | 0                              | 117                            |
| dpd_m05                           | BIGINT        |              7.01 |             112 | 0                              | 114                            |
| dpd_m06                           | BIGINT        |              9.53 |             112 | 0                              | 117                            |
| dpd_m07                           | BIGINT        |             12.04 |             103 | 0                              | 113                            |
| dpd_m08                           | BIGINT        |             14.15 |             116 | 0                              | 119                            |
| dpd_m09                           | BIGINT        |             16.32 |              98 | 0                              | 113                            |
| dpd_m10                           | BIGINT        |             18.27 |              98 | 0                              | 113                            |
| dpd_m11                           | BIGINT        |             20.05 |             101 | 0                              | 108                            |
| dpd_m12                           | BIGINT        |             21.83 |              98 | 0                              | 114                            |
| src_system                        | VARCHAR       |              0    |               1 | CARDS                          | CARDS                          |
| batch_id                          | VARCHAR       |              0    |            4404 | CRD_20170405_01                | CRD_20260928_01                |
| extract_ts                        | TIMESTAMP     |              0    |            3644 | 2017-04-05 03:10:00            | 2026-09-28 03:10:00            |
| src_file_name                     | VARCHAR       |              0    |            3570 | crd_acct_mstr_20170405.csv     | crd_acct_mstr_20260928.csv     |
| record_hash                       | VARCHAR       |              0    |          186143 | 0000005568f135d9bc7bcfbfa263c1 | ffffadd7e318537da193ede75e4701 |
| utilisation_m01                   | DOUBLE        |              0    |           10842 | -0.5261                        | 1.3563                         |
| utilisation_m02                   | DOUBLE        |              0.61 |            9077 | 0.0263                         | 1.3267                         |
| utilisation_m03                   | DOUBLE        |              2.98 |            8736 | 0.0169                         | 1.3028                         |
| utilisation_m04                   | DOUBLE        |              5.39 |            9521 | 0.0143                         | 1.2794                         |
| utilisation_m05                   | DOUBLE        |              7.92 |            8970 | 0.0128                         | 1.0726                         |
| utilisation_m06                   | DOUBLE        |             10.48 |            7502 | 0.0109                         | 1.0028                         |
| utilisation_m07                   | DOUBLE        |             12.87 |            7401 | 0.0093                         | 0.9322                         |
| utilisation_m08                   | DOUBLE        |             14.94 |            6393 | 0.0068                         | 0.9156                         |
| utilisation_m09                   | DOUBLE        |             17.02 |            5574 | 0.0082                         | 0.783                          |
| utilisation_m10                   | DOUBLE        |             18.89 |            5049 | 0.0071                         | 0.7179                         |
| utilisation_m11                   | DOUBLE        |             20.65 |            5113 | 0.0076                         | 0.6956                         |
| utilisation_m12                   | DOUBLE        |             22.39 |            4874 | 0.0048                         | 0.7057                         |
| cash_advance_count_90d            | BIGINT        |              0    |               3 | 0                              | 2                              |
| largest_purchase_30d              | DOUBLE        |             29.48 |           48167 | 2.19                           | 4776.02                        |
| top_mcc_category_30d              | VARCHAR       |             29.36 |               6 | fuel                           | utilities                      |

## card_statements (7,531,283 rows)

| column_name                    | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:-------------------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| card_account_id                | VARCHAR       |              0    |          212771 | C-100005                       | C-999991                       |
| statement_date                 | DATE          |              0    |            3908 | 2016-03-23                     | 2026-09-28                     |
| cycle_no                       | BIGINT        |              0    |             406 | 0                              | 377                            |
| cycle_start_date               | DATE          |              0    |            3829 | 2016-02-23                     | 2026-08-29                     |
| due_date                       | DATE          |              0    |            3707 | 2016-04-13                     | 2026-10-19                     |
| opening_balance                | DOUBLE        |              0    |          118264 | 1.89                           | 47949.38                       |
| purchases_amount               | DOUBLE        |              0    |          100469 | 0.0                            | 31075.47                       |
| cash_advances_amount           | DOUBLE        |              0    |             195 | 0.0                            | 4990.0                         |
| payments_amount                | DOUBLE        |              0    |           79612 | 0.0                            | 27193.79                       |
| interest_amount                | DOUBLE        |              0    |            9519 | 0.0                            | 804.77                         |
| fees_amount                    | DOUBLE        |              0    |               7 | 0.0                            | 184.0                          |
| fees_reversed_amount           | DOUBLE        |              0    |               1 | 0.0                            | 0.0                            |
| closing_balance                | DOUBLE        |              0    |          134259 | -190.76                        | 48897.18                       |
| credit_limit_at_statement      | DOUBLE        |              0    |              93 | 500.0                          | 50000.0                        |
| minimum_due                    | DOUBLE        |              0    |           20792 | 0.0                            | 9341.71                        |
| past_due_included              | DOUBLE        |              0    |            4492 | 0.0                            | 7879.27                        |
| amount_paid_by_due             | DOUBLE        |              5.75 |           99696 | 0.0                            | 31075.47                       |
| min_paid_flag                  | BOOLEAN       |              0    |               2 | false                          | true                           |
| paid_in_full_flag              | BOOLEAN       |              0    |               2 | false                          | true                           |
| first_payment_after_due_date   | DATE          |             98.21 |             957 | 2016-11-03                     | 2026-09-27                     |
| days_late                      | BIGINT        |             98.57 |             122 | 1                              | 181                            |
| cycles_delinquent_at_statement | BIGINT        |              0    |               7 | 0                              | 6                              |
| dpd_at_statement               | BIGINT        |              0    |              27 | 0                              | 163                            |
| estatement_flag                | BOOLEAN       |              0    |               2 | false                          | true                           |
| batch_id                       | VARCHAR       |              0    |             145 | CRD_STMT_201603                | CRD_STMT_202609                |
| filename                       | VARCHAR       |              0    |             210 | D:\iiith\maple_data\maple_coll | D:\iiith\maple_data\maple_coll |
| year                           | BIGINT        |              0    |              12 | 2016                           | 2026                           |

## case_assignment_history (423,830 rows)

| column_name                       | column_type   |   null_percentage |   approx_unique | min                 | max                 |
|:----------------------------------|:--------------|------------------:|----------------:|:--------------------|:--------------------|
| assignment_id                     | VARCHAR       |              0    |          249852 | AS-0000005          | AS-9521016          |
| case_id                           | VARCHAR       |              0    |          166050 | CS-2016-101365      | CS-2026-999997      |
| agent_id                          | VARCHAR       |              0    |             848 | AG-1003             | AG-9999             |
| team_id                           | VARCHAR       |              0    |              73 | CGY-EARLY-1         | WIN-REC-3           |
| queue                             | VARCHAR       |              0    |               4 | early_stage         | recoveries          |
| assigned_ts                       | TIMESTAMP     |              0    |          168333 | 2016-10-03 08:56:01 | 2026-09-27 09:59:55 |
| unassigned_ts                     | TIMESTAMP     |             19.29 |            3422 | 2016-10-06 08:00:00 | 2026-09-27 08:00:00 |
| assignment_reason                 | VARCHAR       |              0    |               7 | agent_absent        | vulnerability       |
| assignment_method                 | VARCHAR       |              0    |               3 | manual              | rule_router         |
| routing_rule_id                   | VARCHAR       |             26.38 |              13 | RR-EARLY-01         | RR-VUL-01           |
| continuity_flag                   | BOOLEAN       |              0    |               2 | false               | true                |
| language_match_flag               | BOOLEAN       |              0    |               2 | false               | true                |
| certified_for_vulnerable_flag     | BOOLEAN       |              0    |               2 | false               | true                |
| dpd_at_assignment                 | BIGINT        |              0    |              32 | 0                   | 91                  |
| overdue_at_assignment             | DOUBLE        |              0    |           80236 | 0.0                 | 27679.68            |
| hardship_flag_at_assignment       | BOOLEAN       |              0    |               2 | false               | true                |
| agent_case_load_at_assignment     | BIGINT        |              0    |              90 | 105                 | 200                 |
| agent_cure_rate_90d_at_assignment | DOUBLE        |              0    |            3646 | 0.08                | 0.5501              |
| contacts_during                   | BIGINT        |              0    |              27 | 0                   | 25                  |
| rpcs_during                       | BIGINT        |              0    |              20 | 0                   | 17                  |
| ptps_during                       | BIGINT        |              0    |               6 | 0                   | 5                   |
| payments_during_amount            | DOUBLE        |              0    |           15265 | 0.0                 | 8233.19             |
| complaint_during_flag             | BOOLEAN       |              0    |               2 | false               | true                |

## channel_capacity (287 rows)

| column_name        | column_type   |   null_percentage |   approx_unique | min        | max               |
|:-------------------|:--------------|------------------:|----------------:|:-----------|:------------------|
| date               | DATE          |              0    |              34 | 2026-09-01 | 2026-10-11        |
| channel            | VARCHAR       |              0    |               5 | call       | sms               |
| time_band          | VARCHAR       |              0    |               4 | 08-12      | all_day           |
| capacity_units     | BIGINT        |              0    |              67 | 0          | 60000             |
| capacity_unit_type | VARCHAR       |              0    |               3 | letters    | outbound_attempts |
| used_units         | BIGINT        |             34.15 |             157 | 0          | 5809              |
| unit_cost_cad      | DOUBLE        |              0    |               3 | 0.001      | 2.4               |
| daily_budget_cad   | BIGINT        |             57.14 |               3 | 30         | 400               |
| vendor             | VARCHAR       |             42.86 |               4 | VEN-ESP-02 | VEN-SMS-01        |
| outage_flag        | BOOLEAN       |              0    |               2 | false      | true              |
| ops_event_id       | VARCHAR       |             97.91 |               1 | INC-0923   | INC-0923          |

## code_lookups (113 rows)

| column_name     | column_type   |   null_percentage |   approx_unique | min                            | max                           |
|:----------------|:--------------|------------------:|----------------:|:-------------------------------|:------------------------------|
| code_type       | VARCHAR       |              0    |              11 | block_code                     | strategy_code                 |
| code            | VARCHAR       |              0    |             137 | A                              | Z                             |
| description_en  | VARCHAR       |              0    |             102 | Bankruptcy / insolvency block  | Wrong number                  |
| description_fr  | VARCHAR       |             84.07 |              20 | Avis de décès                  | Événement système             |
| attributes_json | VARCHAR       |             65.49 |              12 | {"annual_fee": 0.0, "purchase_ | {"text": "Reminder from Maple |
| active_flag     | BOOLEAN       |              0    |               1 | true                           | true                          |
| effective_from  | DATE          |              0    |               9 | 2019-01-01                     | 2026-02-01                    |

## collections_cases (367,229 rows)

| column_name                 | column_type   |   null_percentage |   approx_unique | min                            | max                          |
|:----------------------------|:--------------|------------------:|----------------:|:-------------------------------|:-----------------------------|
| case_id                     | VARCHAR       |              0    |          228613 | CS-2016-101691                 | CS-2026-999995               |
| coll_customer_ref           | VARCHAR       |              0    |          178527 | AAA-2758                       | ZOZ-9589                     |
| case_open_date              | DATE          |              0    |            3838 | 2016-10-02                     | 2026-09-28                   |
| case_open_reason            | VARCHAR       |              0    |               4 | manual                         | returned_pad                 |
| case_status                 | VARCHAR       |              0    |               9 | charged_off                    | settled                      |
| case_status_date            | DATE          |              0    |            3838 | 2016-10-11                     | 2026-09-28                   |
| primary_account_id          | VARCHAR       |              0    |          162106 | C-100000                       | L-9999986                    |
| primary_product             | VARCHAR       |              0    |               6 | auto_loan                      | personal_loan                |
| account_ids                 | VARCHAR       |              0    |          169299 | C-100048                       | ["L-9999986"]                |
| accounts_in_case_count      | BIGINT        |              0    |               2 | 1                              | 2                            |
| entry_dpd                   | BIGINT        |              0    |               1 | 1                              | 1                            |
| current_dpd                 | BIGINT        |              0    |             207 | 0                              | 181                          |
| max_dpd_episode             | BIGINT        |              0    |             205 | 1                              | 181                          |
| current_bucket              | VARCHAR       |              0    |               9 | 1-30                           | current                      |
| bucket_entry_date           | DATE          |              0    |            3838 | 2016-10-11                     | 2026-09-28                   |
| prior_bucket                | VARCHAR       |              0    |               7 | 1-30                           | current                      |
| bucket_path                 | VARCHAR       |              0    |              11 | current>1-30                   | current>1-30>current         |
| total_overdue               | DOUBLE        |              0    |           53579 | 0.0                            | 36906.24                     |
| total_exposure              | DOUBLE        |              0    |          137026 | 0.0                            | 1457213.32                   |
| entry_overdue               | DOUBLE        |              0    |           65388 | 0.0                            | 9748.31                      |
| queue                       | VARCHAR       |              0    |               6 | early_stage                    | special_handling             |
| assigned_team               | VARCHAR       |              0    |              94 | CGY-EARLY-1                    | WIN-SPEC-3                   |
| assigned_agent_id           | VARCHAR       |             23.59 |             848 | AG-1003                        | AG-9999                      |
| assignment_date             | DATE          |             23.59 |            3838 | 2016-10-03                     | 2026-09-27                   |
| language_of_service         | VARCHAR       |              0    |               2 | EN                             | FR                           |
| strategy_code               | VARCHAR       |              0    |               7 | EARLY-CALL-SMSLINK             | REC-DEBT-SALE                |
| strategy_version            | VARCHAR       |              0    |               3 | v2.4                           | v3.2                         |
| test_cell                   | VARCHAR       |              0    |               4 | challenger_A                   | no_contact_holdout           |
| assignment_method           | VARCHAR       |              0    |               2 | random                         | rule_based                   |
| treatment_path              | VARCHAR       |             11.86 |            5666 | CALL                           | SMS>PUSH>SMS>PUSH>SMS>LETTER |
| current_treatment           | VARCHAR       |              0    |               9 | agent_call                     | sms_reminder                 |
| next_scheduled_action       | VARCHAR       |             76.79 |               2 | outbound_call                  | sms_reminder                 |
| next_action_ts              | TIMESTAMP     |             76.79 |              38 | 2026-09-29 09:00:00            | 2026-10-02 19:00:00          |
| contact_attempts_total      | BIGINT        |              0    |              43 | 0                              | 45                           |
| rpc_count                   | BIGINT        |              0    |              26 | 0                              | 25                           |
| last_contact_ts             | TIMESTAMP     |             11.86 |          149453 | 2016-10-08 09:58:14            | 2026-09-27 22:48:21          |
| last_rpc_ts                 | TIMESTAMP     |             40.64 |          101766 | 2016-10-10 15:42:02            | 2026-09-27 22:53:46          |
| last_contact_channel        | VARCHAR       |             11.86 |               5 | call                           | sms                          |
| promises_total              | BIGINT        |              0    |               9 | 0                              | 7                            |
| promises_kept               | BIGINT        |              0    |               5 | 0                              | 4                            |
| promises_broken             | BIGINT        |              0    |               7 | 0                              | 6                            |
| promises_open               | BIGINT        |              0    |               2 | 0                              | 1                            |
| current_ptp_id              | VARCHAR       |             91.06 |           17644 | PTP-0009768                    | PTP-9511691                  |
| current_ptp_amount          | DOUBLE        |             91.06 |            2504 | 1.69                           | 15015.0                      |
| current_ptp_due_date        | DATE          |             91.06 |              25 | 2026-09-24                     | 2026-10-18                   |
| payments_since_open_amount  | DOUBLE        |              0    |           64069 | 0.0                            | 32560.92                     |
| payments_since_open_count   | BIGINT        |              0    |               9 | 0                              | 7                            |
| cure_flag                   | BOOLEAN       |              0    |               2 | false                          | true                         |
| cure_date                   | DATE          |             27.34 |            3838 | 2016-10-11                     | 2026-09-15                   |
| days_to_cure                | BIGINT        |             27.34 |             121 | 0                              | 119                          |
| recidivism_flag             | BOOLEAN       |              0    |               2 | false                          | true                         |
| prior_cases_12m             | BIGINT        |              0    |               5 | 0                              | 4                            |
| hardship_flag               | BOOLEAN       |              0    |               2 | false                          | true                         |
| hardship_source             | VARCHAR       |             87.19 |               3 | agent_coded                    | model                        |
| hardship_reason             | VARCHAR       |             87.19 |              12 | bereavement                    | strike_lockout               |
| hardship_program_offered    | BOOLEAN       |             87.19 |               2 | false                          | true                         |
| hardship_program_accepted   | BOOLEAN       |             90.07 |               2 | false                          | true                         |
| hardship_plan_type          | VARCHAR       |             95.4  |               7 | debt_management_plan           | term_extension               |
| hardship_plan_start         | DATE          |             95.4  |            1255 | 2016-11-11                     | 2026-10-30                   |
| hardship_plan_end           | DATE          |             95.4  |            1896 | 2017-03-16                     | 2030-10-05                   |
| payment_plan_flag           | BOOLEAN       |              0    |               2 | false                          | true                         |
| plan_instalment_amount      | DOUBLE        |             97.77 |            2516 | 25.0                           | 3120.49                      |
| plan_instalments_total      | BIGINT        |             97.77 |               3 | 6                              | 48                           |
| plan_instalments_paid       | BIGINT        |             97.77 |              43 | 0                              | 48                           |
| settlement_offered_flag     | BOOLEAN       |              0    |               2 | false                          | true                         |
| settlement_amount           | DOUBLE        |             97.85 |            4030 | 400.04                         | 27706.86                     |
| settlement_pct              | DOUBLE        |             97.85 |            2156 | 0.4                            | 0.7                          |
| dispute_flag                | BOOLEAN       |              0    |               2 | false                          | true                         |
| dispute_type                | VARCHAR       |             95.84 |               4 | billing_error                  | payment_not_applied          |
| dispute_date                | DATE          |             95.84 |            2200 | 2016-10-10                     | 2026-10-08                   |
| dispute_status              | VARCHAR       |             95.84 |               3 | open                           | resolved_customer            |
| complaint_flag              | BOOLEAN       |              0    |               2 | false                          | true                         |
| complaint_date              | DATE          |             96.86 |            1906 | 2016-10-10                     | 2026-10-18                   |
| complaint_stage             | VARCHAR       |             96.86 |               4 | FCAC                           | frontline                    |
| cease_contact_flag          | BOOLEAN       |              0    |               2 | false                          | true                         |
| third_party_rep_flag        | BOOLEAN       |              0    |               2 | false                          | true                         |
| insolvency_hold_flag        | BOOLEAN       |              0    |               2 | false                          | true                         |
| deceased_hold_flag          | BOOLEAN       |              0    |               1 | false                          | false                        |
| vulnerable_customer_flag    | BOOLEAN       |              0    |               2 | false                          | true                         |
| skip_trace_flag             | BOOLEAN       |              0    |               2 | false                          | true                         |
| skip_trace_status           | VARCHAR       |             98.45 |               3 | found                          | pending                      |
| agency_placement_flag       | BOOLEAN       |              0    |               2 | false                          | true                         |
| agency_name                 | VARCHAR       |             99.26 |               2 | Maple Credit Solutions         | Northern Recovery Services   |
| agency_placement_date       | DATE          |             99.26 |             683 | 2017-07-02                     | 2026-09-27                   |
| legal_referral_flag         | BOOLEAN       |              0    |               2 | false                          | true                         |
| legal_status                | VARCHAR       |             98.4  |               4 | demand_letter                  | statement_of_claim           |
| repossession_initiated_flag | BOOLEAN       |              0    |               2 | false                          | true                         |
| chargeoff_flag              | BOOLEAN       |              0    |               2 | false                          | true                         |
| chargeoff_date              | DATE          |             98.92 |            1592 | 2017-06-02                     | 2026-09-25                   |
| chargeoff_amount            | DOUBLE        |             98.9  |            2322 | 0.0                            | 769713.05                    |
| recovered_post_chargeoff    | DOUBLE        |             98.9  |            1029 | 0.0                            | 757362.5                     |
| province_code               | VARCHAR       |              0    |              12 | AB                             | YT                           |
| contact_rule_set            | VARCHAR       |              0    |              15 | AB-STD-2026                    | YT-STD-2026                  |
| contact_cap_7d              | BIGINT        |              0    |               1 | 3                              | 3                            |
| contacts_last_7d            | BIGINT        |              0    |               9 | 0                              | 7                            |
| contact_cap_breach_count    | BIGINT        |              0    |               9 | 0                              | 7                            |
| out_of_hours_contact_count  | BIGINT        |              0    |               5 | 0                              | 4                            |
| days_in_collections         | BIGINT        |              0    |             203 | 0                              | 180                          |
| cost_to_collect_est         | DOUBLE        |              0    |            5000 | 0.0                            | 94.04                        |
| expected_loss_est           | DOUBLE        |              0    |           41092 | 0.0                            | 479349.67                    |
| escalation_flag             | BOOLEAN       |              0    |               2 | false                          | true                         |
| escalation_reason           | VARCHAR       |             93.66 |               5 | abusive_customer               | vulnerability                |
| supervisor_review_flag      | BOOLEAN       |              0    |               2 | false                          | true                         |
| human_override_flag         | BOOLEAN       |              0    |               2 | false                          | true                         |
| override_reason             | VARCHAR       |             92.02 |               5 | Agent judgement: customer trav | Promise already in place     |
| nba_recommendation_last     | VARCHAR       |             20.06 |               5 | call_daytime                   | sms_payment_link             |
| nba_accepted_flag           | BOOLEAN       |             20.06 |               2 | false                          | true                         |
| notes_count                 | BIGINT        |              0    |              29 | 0                              | 30                           |
| last_note_id                | VARCHAR       |             35.97 |          104710 | N-0000005                      | N-9537268                    |
| qa_flag_count               | BIGINT        |              0    |               7 | 0                              | 6                            |
| outcome                     | VARCHAR       |             26.24 |               3 | charged_off                    | settled                      |
| outcome_date                | DATE          |             26.24 |            3838 | 2016-10-11                     | 2026-09-25                   |
| roll_forward_count          | BIGINT        |              0    |               7 | 0                              | 6                            |
| roll_back_count             | BIGINT        |              0    |               2 | 0                              | 1                            |
| dpd_at_day_7                | BIGINT        |              2.57 |               2 | 0                              | 8                            |
| overdue_at_day_7            | DOUBLE        |              2.57 |           61720 | 0.0                            | 9748.31                      |
| dpd_at_day_14               | BIGINT        |              4.83 |               5 | 0                              | 15                           |
| overdue_at_day_14           | DOUBLE        |              4.83 |           57186 | 0.0                            | 9748.31                      |
| dpd_at_day_21               | BIGINT        |              7.28 |              13 | 0                              | 22                           |
| overdue_at_day_21           | DOUBLE        |              7.28 |           52719 | 0.0                            | 9298.41                      |
| dpd_at_day_30               | BIGINT        |             10.01 |              24 | 0                              | 31                           |
| overdue_at_day_30           | DOUBLE        |             10.01 |           57339 | 0.0                            | 18596.82                     |
| dpd_at_day_45               | BIGINT        |             14.49 |              34 | 0                              | 46                           |
| overdue_at_day_45           | DOUBLE        |             14.49 |           36180 | 0.0                            | 18453.12                     |
| dpd_at_day_60               | BIGINT        |             18.96 |              48 | 0                              | 61                           |
| overdue_at_day_60           | DOUBLE        |             18.96 |           29272 | 0.0                            | 19812.72                     |
| dpd_at_day_90               | BIGINT        |             26.26 |              69 | 0                              | 91                           |
| overdue_at_day_90           | DOUBLE        |             26.26 |           20789 | 0.0                            | 27679.68                     |
| src_system                  | VARCHAR       |              0    |               1 | COLLX                          | COLLX                        |
| batch_id                    | VARCHAR       |              0    |               1 | COLLX_20260928                 | COLLX_20260928               |
| extract_ts                  | TIMESTAMP     |              0    |               1 | 2026-09-28 04:30:00            | 2026-09-28 04:30:00          |
| record_hash                 | VARCHAR       |            100    |               0 | nan                            | nan                          |

## contact_history (2,688,337 rows)

| column_name                     | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:--------------------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| contact_id                      | VARCHAR       |              0    |          209619 | CT-0000007                     | CT-9632958                     |
| source_platform                 | VARCHAR       |              0    |               7 | app_push                       | web_chat                       |
| case_id                         | VARCHAR       |              0    |          132174 | CS-2016-101691                 | CS-2026-999995                 |
| crm_customer_id                 | VARCHAR       |              1.01 |          106649 | AAA-2567                       | ZOZ-9840                       |
| account_id                      | VARCHAR       |             19.9  |          110680 | C-100000                       | L-9999967                      |
| agent_id                        | VARCHAR       |             62    |             848 | AG-1003                        | AG-9999                        |
| campaign_id                     | VARCHAR       |             33.07 |            7583 | B1-CALL-0102                   | WO-SMS-0903                    |
| strategy_code                   | VARCHAR       |              5.05 |               7 | EARLY-CALL-SMSLINK             | REC-DEBT-SALE                  |
| test_cell                       | VARCHAR       |              5    |               4 | challenger_A                   | no_contact_holdout             |
| treatment_code                  | VARCHAR       |             29.52 |               5 | email_reminder                 | push                           |
| direction                       | VARCHAR       |              0    |               3 | inbound                        | outbound                       |
| channel                         | VARCHAR       |              0.71 |               9 | call                           | system                         |
| channel_v2                      | VARCHAR       |             98.85 |               9 | call                           | system                         |
| sub_channel                     | VARCHAR       |             22.06 |              10 | chat_web                       | sms_2way                       |
| contact_ts_utc                  | TIMESTAMP     |              0    |          197612 | 2016-10-09 02:52:05            | 2026-09-28 05:52:32            |
| contact_ts_local                | TIMESTAMP     |              0    |          182890 | 2016-10-08 19:52:05            | 2026-09-27 23:59:48            |
| customer_time_zone              | VARCHAR       |              2.02 |               9 | America/Edmonton               | America/Yellowknife            |
| day_of_week                     | VARCHAR       |              0    |               7 | Fri                            | Wed                            |
| stat_holiday_flag               | BOOLEAN       |              0    |               2 | false                          | true                           |
| within_permitted_hours_flag     | BOOLEAN       |              0    |               2 | false                          | true                           |
| attempt_number_case             | BIGINT        |             29.52 |              43 | 1                              | 42                             |
| attempt_number_day              | BIGINT        |             29.52 |               4 | 1                              | 4                              |
| contacts_prior_7d               | BIGINT        |              0    |               9 | 0                              | 7                              |
| consent_status_at_time          | VARCHAR       |              0    |               2 | granted                        | unknown                        |
| dialer_mode                     | VARCHAR       |             69.23 |               4 | manual                         | progressive                    |
| phone_number_hash               | VARCHAR       |             69.23 |           48515 | 0000f7dc7cfcb3bfbbd5f7a2b08145 | fffff0cd2ec9f0dab5fa835ebe3532 |
| phone_type_dialled              | VARCHAR       |             69.23 |               3 | landline                       | work                           |
| dial_result                     | VARCHAR       |             61.3  |               6 | abandoned                      | wrong_number                   |
| amd_result                      | VARCHAR       |             69.23 |               3 | human                          | unknown                        |
| ring_duration_sec               | BIGINT        |             69.23 |              39 | 3                              | 40                             |
| queue_wait_sec                  | BIGINT        |             61.3  |             442 | 0                              | 400                            |
| talk_duration_sec               | BIGINT        |             61.3  |            1286 | 0                              | 2945                           |
| hold_duration_sec               | BIGINT        |             77.45 |              78 | 0                              | 90                             |
| wrap_duration_sec               | BIGINT        |             77.45 |              78 | 110                            | 190                            |
| abandoned_flag                  | BOOLEAN       |             69.23 |               2 | false                          | true                           |
| rpc_flag                        | BOOLEAN       |              0    |               2 | false                          | true                           |
| third_party_contact_flag        | BOOLEAN       |              0    |               2 | false                          | true                           |
| identity_verified_flag          | BOOLEAN       |             77.45 |               2 | false                          | true                           |
| recording_notice_read_flag      | BOOLEAN       |             77.45 |               2 | false                          | true                           |
| agent_identified_self_flag      | BOOLEAN       |             77.45 |               2 | false                          | true                           |
| language_used                   | VARCHAR       |              4.98 |               3 | EN                             | other                          |
| interpreter_used_flag           | BOOLEAN       |              0    |               2 | false                          | true                           |
| outcome_code                    | VARCHAR       |              0    |              13 | BKPT                           | WN                             |
| outcome_desc                    | VARCHAR       |              0    |              16 | Bankruptcy / proposal advised  | Wrong number                   |
| sub_outcome_code                | VARCHAR       |             98.5  |               2 | DISP                           | HARD                           |
| ptp_made_flag                   | BOOLEAN       |              0    |               2 | false                          | true                           |
| ptp_id                          | VARCHAR       |             90.56 |           13667 | PTP-0000005                    | PTP-9511658                    |
| payment_taken_flag              | BOOLEAN       |              0    |               2 | false                          | true                           |
| payment_amount                  | DOUBLE        |             99.25 |            1208 | 3.12                           | 4396.48                        |
| payment_method                  | VARCHAR       |             99.25 |               4 | debit_card                     | pad                            |
| dispute_raised_flag             | BOOLEAN       |              0    |               2 | false                          | true                           |
| complaint_raised_flag           | BOOLEAN       |              0    |               2 | false                          | true                           |
| hardship_mentioned_flag         | BOOLEAN       |              0    |               2 | false                          | true                           |
| vulnerability_disclosed_flag    | BOOLEAN       |              0    |               2 | false                          | true                           |
| cease_request_flag              | BOOLEAN       |              0    |               2 | false                          | true                           |
| callback_requested_flag         | BOOLEAN       |              0    |               2 | false                          | true                           |
| callback_ts                     | TIMESTAMP     |             98.54 |            2836 | 2016-12-22 19:42:41            | 2026-09-29 17:56:20            |
| transferred_flag                | BOOLEAN       |              0    |               2 | false                          | true                           |
| transfer_target                 | VARCHAR       |             98.12 |               3 | french_queue                   | supervisor                     |
| agent_coded_sentiment           | VARCHAR       |             81.27 |               4 | hostile                        | positive                       |
| call_recording_id               | VARCHAR       |             73.81 |           48879 | REC-0000007                    | REC-9626601                    |
| transcript_id                   | VARCHAR       |             99.01 |            1578 | 10007                          | 9511245                        |
| voice_sample_id                 | VARCHAR       |             99.92 |             174 | VS-1010101                     | VS-9511202                     |
| note_id                         | VARCHAR       |             70.69 |           70981 | N-0000004                      | N-9537262                      |
| sms_template_id                 | VARCHAR       |             88.42 |               2 | SMS-REM-EN-02                  | SMS-REM-FR-01                  |
| sms_text                        | VARCHAR       |             88.42 |           24351 | Rappel de la Banque Maple : un | Reminder from Maple Bank: a pa |
| sms_delivered_flag              | BOOLEAN       |             88.42 |               2 | false                          | true                           |
| sms_delivered_ts                | TIMESTAMP     |             89.24 |           19611 | 2016-10-19 19:44:36            | 2026-09-27 19:42:44            |
| sms_reply_flag                  | BOOLEAN       |             88.42 |               2 | false                          | true                           |
| sms_reply_text                  | VARCHAR       |             99.34 |              11 | ARRET                          | 👍                              |
| sms_opt_out_flag                | BOOLEAN       |             88.42 |               2 | false                          | true                           |
| payment_link_id                 | VARCHAR       |             77.44 |           28108 | PL-0001                        | PL-ffff                        |
| link_clicked_flag               | BOOLEAN       |             76.24 |               2 | false                          | true                           |
| link_click_ts                   | TIMESTAMP     |             97.1  |            6302 | 2016-11-03 11:05:02            | 2026-09-28 19:03:53            |
| link_payment_flag               | BOOLEAN       |             76.24 |               2 | false                          | true                           |
| email_template_id               | VARCHAR       |             87.82 |               2 | EM-REM-EN-01                   | EM-REM-FR-01                   |
| email_subject                   | VARCHAR       |             87.82 |               6 | Action needed on your account  | Your payment is past due       |
| email_delivered_flag            | BOOLEAN       |             87.82 |               2 | false                          | true                           |
| email_opened_flag               | BOOLEAN       |             87.82 |               2 | false                          | true                           |
| email_open_ts                   | TIMESTAMP     |             94.95 |           11358 | 2016-10-20 00:41:30            | 2026-09-29 05:49:00            |
| email_clicked_flag              | BOOLEAN       |             87.82 |               2 | false                          | true                           |
| email_bounce_type               | VARCHAR       |             99.64 |               2 | hard                           | soft                           |
| email_unsubscribe_flag          | BOOLEAN       |             87.82 |               2 | false                          | true                           |
| push_template_id                | VARCHAR       |             97.49 |               1 | PU-REM-01                      | PU-REM-01                      |
| push_delivered_flag             | BOOLEAN       |             97.49 |               2 | false                          | true                           |
| push_opened_flag                | BOOLEAN       |             97.49 |               2 | false                          | true                           |
| app_session_after_contact_flag  | BOOLEAN       |             73.73 |               2 | false                          | true                           |
| app_payment_after_contact_flag  | BOOLEAN       |             73.73 |               2 | false                          | true                           |
| letter_template_id              | VARCHAR       |             86.56 |              16 | LTR-DLQ120-EN                  | LTR-DLQWO-FR                   |
| letter_mailed_date              | DATE          |             86.56 |            2855 | 2016-10-14                     | 2026-09-27                     |
| letter_returned_flag            | BOOLEAN       |             86.56 |               2 | false                          | true                           |
| ivr_path                        | VARCHAR       |             96.88 |               5 | 1>2                            | 3                              |
| ivr_self_serve_payment_flag     | BOOLEAN       |             96.88 |               2 | false                          | true                           |
| chat_session_id                 | VARCHAR       |             99.39 |            1293 | CH-100652                      | CH-999236                      |
| chat_message_count              | BIGINT        |             99.39 |              26 | 4                              | 30                             |
| inbound_reason                  | VARCHAR       |             88.34 |               5 | balance_query                  | payment                        |
| contact_cost_cad                | DOUBLE        |              0    |             223 | 0.0                            | 4.0                            |
| vendor_id                       | VARCHAR       |             60.29 |               4 | VEN-ESP-02                     | VEN-SMS-01                     |
| qa_selected_flag                | BOOLEAN       |             61.3  |               2 | false                          | true                           |
| qa_score                        | BIGINT        |             99.55 |              41 | 46                             | 100                            |
| qa_reviewer_id                  | VARCHAR       |             99.55 |              17 | AG-1304                        | AG-9637                        |
| system_event_type               | VARCHAR       |             82.14 |               3 | bucket_change                  | ptp_kept                       |
| ops_incident_id                 | VARCHAR       |             99.63 |               2 | INC-0914                       | INC-0923                       |
| src_system                      | VARCHAR       |              0    |               9 | CHAT                           | SMSGW                          |
| batch_id                        | VARCHAR       |              0    |               1 | CH_20260928                    | CH_20260928                    |
| extract_ts                      | TIMESTAMP     |              0    |               1 | 2026-09-28 05:00:00            | 2026-09-28 05:00:00            |
| src_file_name                   | VARCHAR       |              0    |            3916 | contact_history_20161008.csv   | contact_history_20260927.csv   |
| record_hash                     | VARCHAR       |            100    |               0 | nan                            | nan                            |
| contact_hour_local              | BIGINT        |              0    |              18 | 5                              | 23                             |
| minutes_since_prev_contact      | BIGINT        |             13.84 |           25134 | -816                           | 329897                         |
| days_since_case_open_at_contact | BIGINT        |              0    |             340 | -2                             | 300                            |
| dpd_at_contact                  | BIGINT        |              0    |             332 | 0                              | 301                            |
| bucket_at_contact               | VARCHAR       |              0    |               9 | 1-30                           | current                        |
| overdue_at_contact              | DOUBLE        |              0    |           70458 | 0.0                            | 27679.68                       |
| open_ptp_at_contact_flag        | BOOLEAN       |              0    |               2 | false                          | true                           |
| broken_ptp_count_at_contact     | BIGINT        |              0    |               7 | 0                              | 6                              |
| rpc_count_prior_30d             | BIGINT        |              0    |              13 | 0                              | 11                             |
| answer_rate_prior_30d           | DOUBLE        |             52.65 |              37 | 0.0                            | 1.0                            |
| sms_segment_count               | BIGINT        |             88.42 |               2 | 1                              | 2                              |
| message_language                | VARCHAR       |             73.73 |               2 | EN                             | FR                             |
| email_client                    | VARCHAR       |             87.82 |               4 | apple_mail                     | outlook                        |
| device_type                     | VARCHAR       |             73.12 |               3 | android                        | web                            |
| link_expiry_ts                  | TIMESTAMP     |             77.44 |           47413 | 2016-10-22 17:20:50            | 2026-09-30 22:52:32            |
| agent_site                      | VARCHAR       |             62    |               6 | Calgary                        | vendor_offshore                |
| agent_tenure_band_at_contact    | VARCHAR       |             62    |               3 | 2y+                            | <6m                            |
| script_id                       | VARCHAR       |             77.45 |               9 | SCR-EARLY-STD-EN               | SCR-VUL-FR                     |
| disclosure_version              | VARCHAR       |             77.45 |               2 | DISC-2024-01                   | DISC-2026-03                   |
| recording_retention_until       | DATE          |             73.81 |            4310 | 2023-10-09                     | 2033-09-27                     |

## customers (1,020,000 rows)

| column_name                      | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:---------------------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| crm_customer_id                  | VARCHAR       |              0    |          225805 | AAA-1243                       | ZOZ-9971                       |
| customer_uuid                    | VARCHAR       |              0    |          207819 | 00003fa0-4680-4ced-bcdc-8c20f5 | 3fffd630-daa5-4142-8568-1b1d4a |
| record_created_ts                | TIMESTAMP     |              0    |          204932 | 1995-01-06 18:11:38            | 2026-09-23 19:56:05            |
| record_source                    | VARCHAR       |              0    |               3 | branch_onboarding              | online                         |
| salutation                       | VARCHAR       |             12.01 |              21 | DR.                            | mx                             |
| first_name                       | VARCHAR       |              0    |            3023 | AARAV                          | Étienne                        |
| middle_name                      | VARCHAR       |             40    |             959 | A                              | Étienne                        |
| last_name                        | VARCHAR       |              0    |            1765 | Aawd                           | Émond                          |
| preferred_name                   | VARCHAR       |             99.19 |              33 | Alex                           | Will                           |
| full_name_raw                    | VARCHAR       |              0    |          189467 | Aarav A Ahmed                  | Étienne Étienne Morin          |
| name_suffix                      | VARCHAR       |             99.03 |               2 | III                            | Sr.                            |
| date_of_birth                    | DATE          |              0.49 |           20705 | 1940-10-13                     | 2008-09-27                     |
| dob_raw                          | VARCHAR       |              0.49 |           55771 | 01/01/1941                     | Sep 30 2007                    |
| age                              | BIGINT        |              0.49 |              67 | 18                             | 85                             |
| age_band                         | VARCHAR       |              0.49 |               6 | 18-24                          | 65+                            |
| gender_code                      | VARCHAR       |              0.96 |               4 | F                              | X                              |
| marital_status                   | VARCHAR       |              7.99 |               7 | common_law                     | widowed                        |
| national_id_hash                 | VARCHAR       |              6.39 |          187472 | 0000438df39f668b1cdf828e3a313b | ffff7994db1efe9ccc1cea0b30e257 |
| national_id_present_flag         | BOOLEAN       |              0    |               2 | false                          | true                           |
| id_document_type                 | VARCHAR       |              2.02 |              16 | AB_drivers_licence             | provincial_photo_id            |
| citizenship_status               | VARCHAR       |              1.01 |               4 | citizen                        | work_permit                    |
| primary_phone_raw                | VARCHAR       |              1    |          191932 | (204) 200-7463                 | 9059998652                     |
| primary_phone_e164               | VARCHAR       |              1.49 |          178245 | +12042001775                   | +19059998893                   |
| primary_phone_type               | VARCHAR       |              2.03 |               3 | landline                       | voip                           |
| secondary_phone_raw              | VARCHAR       |             65.09 |           72104 | 204-200-1827                   | 905-999-9573                   |
| work_phone_raw                   | VARCHAR       |             85.02 |           32687 | 204-201-6551 x194              | 905-999-5417 x410              |
| email                            | VARCHAR       |              6    |          154168 | AARAVKAUR73@EXAMPLE.CA         | zzielinski@example.com         |
| email_verified_flag              | BOOLEAN       |              6    |               2 | false                          | true                           |
| email_bounce_flag                | BOOLEAN       |              6    |               2 | false                          | true                           |
| address_line1                    | VARCHAR       |              0.48 |          206820 | 1 Bay St                       | 9999 rue Sherbrooke            |
| address_line2                    | VARCHAR       |             79.94 |            6455 | Apt 1                          | Unit 999                       |
| city                             | VARCHAR       |              0.3  |              97 | Abbotsford                     | Yellowknife                    |
| province_code                    | VARCHAR       |              0.19 |              20 | AB                             | YT                             |
| postal_code                      | VARCHAR       |              0.99 |          169465 | A0B 0A0                        | Y1A 9Z5                        |
| postal_code_raw                  | VARCHAR       |              0.99 |          194682 | A0B 0A0                        | y1a7v8                         |
| fsa                              | VARCHAR       |              0.99 |             631 | A0B                            | Y1A                            |
| country_code                     | VARCHAR       |              0    |               2 | CA                             | US                             |
| time_zone                        | VARCHAR       |              0.5  |               9 | America/Edmonton               | America/Yellowknife            |
| address_since_date               | DATE          |              9.95 |           13373 | 1990-01-05                     | 2026-09-08                     |
| returned_mail_flag               | BOOLEAN       |              0    |               2 | false                          | true                           |
| urban_rural                      | VARCHAR       |              0    |               2 | rural                          | urban                          |
| geo_lat                          | DOUBLE        |              0    |          135884 | 42.19686                       | 63.73552                       |
| geo_lon                          | DOUBLE        |              0    |          140621 | -135.07121                     | -52.5508                       |
| employment_status                | VARCHAR       |              0    |               6 | employed_hourly                | unemployed                     |
| occupation_category              | VARCHAR       |             24.41 |               9 | art_culture_recreation_sport   | trades_transport_equipment     |
| industry_naics2                  | VARCHAR       |             24.41 |              17 | 11                             | 91                             |
| employer_name                    | VARCHAR       |             35.34 |           32093 | Algonquin Accounting Group     | Wildrose Trucking Ltée         |
| employment_start_date            | DATE          |             24.41 |           14442 | 1986-11-09                     | 2026-08-29                     |
| pay_frequency                    | VARCHAR       |              0    |               5 | biweekly                       | weekly                         |
| declared_annual_income           | BIGINT        |              7.03 |           20066 | 9000                           | 900000                         |
| income_verified_flag             | BOOLEAN       |              0    |               2 | false                          | true                           |
| income_verified_date             | DATE          |             44.93 |            2299 | 2021-04-07                     | 2026-09-27                     |
| income_source                    | VARCHAR       |              0    |               5 | ei_benefits                    | social_assistance              |
| household_size                   | BIGINT        |             30.11 |               6 | 1                              | 6                              |
| dependants_count                 | BIGINT        |             29.9  |               5 | 0                              | 4                              |
| housing_status                   | VARCHAR       |             10.08 |               4 | own_free                       | with_family                    |
| monthly_housing_cost             | DOUBLE        |             24.96 |          117568 | 0.02                           | 3599.95                        |
| customer_since_date              | DATE          |              0    |           10433 | 1995-01-01                     | 2026-03-31                     |
| tenure_months                    | BIGINT        |              0    |             405 | 5                              | 380                            |
| segment                          | VARCHAR       |              0    |               4 | affluent                       | private_hnw                    |
| sub_segment                      | VARCHAR       |              0    |             494 | AF-HOURLY-AB                   | MM-UNEMP-YT                    |
| newcomer_program_flag            | BOOLEAN       |              0    |               2 | false                          | true                           |
| newcomer_arrival_date            | DATE          |             92.14 |            2165 | 2020-10-03                     | 2026-03-17                     |
| home_branch_transit              | VARCHAR       |              0.99 |             126 | 01120                          | 09961                          |
| home_branch_city                 | VARCHAR       |              0.26 |              93 | Abbotsford                     | Yellowknife                    |
| relationship_manager_id          | VARCHAR       |             88.01 |             287 | RM-0100                        | RM-0400                        |
| product_count                    | BIGINT        |              0    |              11 | 0                              | 9                              |
| has_credit_card                  | BOOLEAN       |              0    |               2 | false                          | true                           |
| has_personal_loan                | BOOLEAN       |              0    |               2 | false                          | true                           |
| has_auto_loan                    | BOOLEAN       |              0    |               2 | false                          | true                           |
| has_line_of_credit               | BOOLEAN       |              0    |               2 | false                          | true                           |
| has_heloc                        | BOOLEAN       |              0    |               2 | false                          | true                           |
| has_mortgage                     | BOOLEAN       |              0    |               2 | false                          | true                           |
| has_chequing                     | BOOLEAN       |              0    |               2 | false                          | true                           |
| has_savings                      | BOOLEAN       |              0    |               2 | false                          | true                           |
| has_registered_investments       | BOOLEAN       |              0    |               2 | false                          | true                           |
| total_relationship_balance       | DOUBLE        |              0    |          121860 | 0.0                            | 2110967.4                      |
| total_credit_exposure            | DOUBLE        |              0    |           93161 | 0.0                            | 1515673.58                     |
| digital_banking_enrolled         | BOOLEAN       |              0    |               2 | false                          | true                           |
| mobile_app_user_flag             | BOOLEAN       |              0    |               2 | false                          | true                           |
| last_login_ts                    | TIMESTAMP     |             20.91 |          164936 | 2026-06-01 00:13:19            | 2026-09-27 23:59:42            |
| logins_30d                       | BIGINT        |              0    |              20 | 0                              | 16                             |
| app_push_enabled                 | BOOLEAN       |              0    |               2 | false                          | true                           |
| estatements_flag                 | BOOLEAN       |              0    |               2 | false                          | true                           |
| internal_risk_grade              | VARCHAR       |              1.99 |              10 | 1                              | 9                              |
| kyc_status                       | VARCHAR       |              0    |               3 | complete                       | refresh_due                    |
| kyc_last_review_date             | DATE          |              0    |            2022 | 2021-10-24                     | 2026-09-27                     |
| aml_risk_rating                  | VARCHAR       |              0    |               3 | high                           | medium                         |
| pep_flag                         | BOOLEAN       |              0    |               2 | false                          | true                           |
| preferred_language               | VARCHAR       |              0    |               7 | AR                             | ZH                             |
| correspondence_language          | VARCHAR       |              0    |               2 | EN                             | FR                             |
| consent_call                     | BOOLEAN       |              0    |               2 | false                          | true                           |
| consent_call_mobile              | BOOLEAN       |              0    |               2 | false                          | true                           |
| consent_autodialer               | BOOLEAN       |              0    |               2 | false                          | true                           |
| consent_sms                      | BOOLEAN       |              0    |               2 | false                          | true                           |
| consent_email                    | BOOLEAN       |              0    |               2 | false                          | true                           |
| consent_push                     | BOOLEAN       |              0    |               2 | false                          | true                           |
| consent_letter                   | BOOLEAN       |              0    |               2 | false                          | true                           |
| casl_express_consent_email       | BOOLEAN       |              0    |               2 | false                          | true                           |
| casl_consent_date                | DATE          |             57.4  |            4748 | 2014-07-01                     | 2026-09-27                     |
| casl_consent_source              | VARCHAR       |             57.4  |               4 | app                            | online_banking                 |
| sms_consent_date                 | DATE          |             39.96 |            4660 | 2015-01-01                     | 2026-09-27                     |
| consent_last_updated_ts          | TIMESTAMP     |              4.99 |          174997 | 2018-01-01 08:12:20            | 2026-09-27 19:58:34            |
| voicemail_permitted              | BOOLEAN       |              0    |               2 | false                          | true                           |
| contact_at_work_permitted        | BOOLEAN       |              0    |               2 | false                          | true                           |
| preferred_channel                | VARCHAR       |             20.08 |               3 | app                            | sms                            |
| preferred_contact_window_start   | VARCHAR       |             34.97 |               3 | 08:00                          | 10:00                          |
| preferred_contact_window_end     | VARCHAR       |             34.97 |               5 | 17:00                          | 21:00                          |
| preferred_contact_days           | VARCHAR       |             34.97 |               3 | Any                            | weekends                       |
| permitted_call_start_local       | VARCHAR       |              0    |               1 | 07:00                          | 07:00                          |
| permitted_call_end_local         | VARCHAR       |              0    |               1 | 21:00                          | 21:00                          |
| sunday_contact_permitted         | BOOLEAN       |              0    |               2 | false                          | true                           |
| national_dncl_flag               | BOOLEAN       |              0    |               2 | false                          | true                           |
| internal_do_not_call_flag        | BOOLEAN       |              0    |               2 | false                          | true                           |
| cease_communication_flag         | BOOLEAN       |              0    |               2 | false                          | true                           |
| cease_communication_date         | DATE          |             97.99 |             920 | 2024-04-11                     | 2026-09-27                     |
| third_party_authorised_flag      | BOOLEAN       |              0    |               2 | false                          | true                           |
| third_party_relationship         | VARCHAR       |             96.05 |               6 | child                          | trustee                        |
| credit_counselling_agency_flag   | BOOLEAN       |              0    |               2 | false                          | true                           |
| power_of_attorney_flag           | BOOLEAN       |              0    |               2 | false                          | true                           |
| legal_representative_flag        | BOOLEAN       |              0    |               2 | false                          | true                           |
| accessibility_needs_flag         | BOOLEAN       |              0    |               2 | false                          | true                           |
| accessibility_type               | VARCHAR       |             96.99 |               6 | braille                        | tty_relay                      |
| vulnerability_flag               | BOOLEAN       |              0    |               2 | false                          | true                           |
| vulnerability_type               | VARCHAR       |             93.89 |               9 | bereavement                    | serious_illness                |
| vulnerability_source             | VARCHAR       |             93.89 |               5 | agent_call                     | third_party                    |
| vulnerability_recorded_date      | DATE          |             93.89 |             749 | 2024-10-28                     | 2026-09-23                     |
| vulnerability_review_date        | DATE          |             93.89 |             775 | 2025-01-26                     | 2026-12-22                     |
| deceased_flag                    | BOOLEAN       |              0    |               2 | false                          | true                           |
| deceased_notified_date           | DATE          |             99    |            1450 | 2017-04-06                     | 2026-09-27                     |
| bankruptcy_flag                  | BOOLEAN       |              0    |               2 | false                          | true                           |
| consumer_proposal_flag           | BOOLEAN       |              0    |               2 | false                          | true                           |
| insolvency_filed_date            | DATE          |             98.73 |            1134 | 2017-03-03                     | 2026-09-28                     |
| licensed_insolvency_trustee_name | VARCHAR       |             98.73 |               7 | Atlantic Trustee Services      | Prairie Insolvency Group       |
| fraud_victim_flag                | BOOLEAN       |              0    |               2 | false                          | true                           |
| marketing_opt_out_flag           | BOOLEAN       |              0    |               2 | false                          | true                           |
| military_or_reserve_flag         | BOOLEAN       |              0    |               2 | false                          | true                           |
| customer_status                  | VARCHAR       |              0    |               5 | active                         | written_off                    |
| duplicate_of_crm_id              | VARCHAR       |             99.43 |            1202 | AAF-7721                       | ZOL-6957                       |
| last_profile_update_ts           | TIMESTAMP     |              0    |          185998 | 2022-08-20 08:02:11            | 2026-09-27 19:51:11            |
| src_system                       | VARCHAR       |              0    |               1 | CRM                            | CRM                            |
| batch_id                         | VARCHAR       |              0    |               1 | CRM_20260928_01                | CRM_20260928_01                |
| extract_ts                       | TIMESTAMP     |              0    |               1 | 2026-09-28 02:00:00            | 2026-09-28 02:00:00            |
| cdc_operation                    | VARCHAR       |              0    |               3 | D                              | U                              |
| record_hash                      | VARCHAR       |            100    |               0 | nan                            | nan                            |
| is_deleted                       | BOOLEAN       |              0    |               2 | false                          | true                           |
| effective_from_ts                | TIMESTAMP     |              0    |          185998 | 2022-08-20 08:02:11            | 2026-09-27 19:51:11            |
| effective_to_ts                  | TIMESTAMP     |              0    |               1 | 9999-12-31 00:00:00            | 9999-12-31 00:00:00            |

## deposit_accounts (780,000 rows)

| column_name                      | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:---------------------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| deposit_account_id               | VARCHAR       |              0    |          196684 | CHQ-100006                     | USD-999345                     |
| snapshot_date                    | DATE          |              0    |            3370 | 2017-04-05                     | 2026-09-28                     |
| snapshot_type                    | VARCHAR       |              0    |               1 | daily                          | month_end                      |
| src_customer_ref                 | VARCHAR       |              0    |          205940 | 0001000771                     | 99999417                       |
| holder_name_raw                  | VARCHAR       |              0    |           93482 | ABBOTT A                       | ZUNIGA V A                     |
| holder_dob_raw                   | VARCHAR       |              2.01 |           24542 | 19401007                       | 20080927                       |
| holder_phone_raw                 | VARCHAR       |              4.05 |          191103 | 2042003711                     | 9059997225                     |
| holder_postal_raw                | VARCHAR       |              0.99 |          155648 | A0B 0G9                        | Y1A 9Z5                        |
| joint_account_flag               | BOOLEAN       |              0    |               2 | false                          | true                           |
| joint_holder_ref                 | VARCHAR       |             81.89 |           33582 | 0001003792                     | 0099995324                     |
| product_type                     | VARCHAR       |              0    |               4 | chequing                       | usd_account                    |
| product_code                     | VARCHAR       |              0    |               7 | BASIC-CHQ                      | USD-SAV                        |
| currency                         | VARCHAR       |              0    |               2 | CAD                            | USD                            |
| institution_number               | VARCHAR       |              0    |               1 | 099                            | 099                            |
| transit_number                   | VARCHAR       |              0    |            8342 | 01000                          | 09999                          |
| open_date                        | DATE          |              0    |            9590 | 1995-05-19                     | 2026-07-30                     |
| account_status                   | VARCHAR       |              0    |               4 | active                         | frozen                         |
| freeze_reason                    | VARCHAR       |             99.54 |               2 | fraud                          | garnishment                    |
| current_balance                  | DOUBLE        |              0    |          110570 | -5287.78                       | 5000.0                         |
| available_balance                | DOUBLE        |              0    |          110696 | -5552.68                       | 9999.99                        |
| hold_amount                      | DOUBLE        |              0    |           14011 | 0.0                            | 799.95                         |
| month_end_balance                | DOUBLE        |              0    |          128725 | -5225.44                       | 5961.3                         |
| avg_daily_balance_mtd            | DOUBLE        |              0    |          120701 | -5213.65                       | 5290.43                        |
| min_balance_mtd                  | DOUBLE        |              0    |          155648 | -5427.45                       | 4999.6                         |
| max_balance_mtd                  | DOUBLE        |              0    |          153428 | -5028.09                       | 6219.8                         |
| overdraft_limit                  | BIGINT        |             83.33 |               5 | 250                            | 5000                           |
| overdraft_used                   | DOUBLE        |             83.33 |            1746 | 0.0                            | 5287.78                        |
| overdraft_protection_flag        | BOOLEAN       |              0    |               2 | false                          | true                           |
| days_negative_mtd                | BIGINT        |              0    |              29 | 0                              | 28                             |
| nsf_count_mtd                    | BIGINT        |              0    |               7 | 0                              | 6                              |
| nsf_fee_mtd                      | BIGINT        |              0    |               6 | 0                              | 288                            |
| returned_pad_count_mtd           | BIGINT        |              0    |               3 | 0                              | 2                              |
| credits_count_mtd                | BIGINT        |              0    |              11 | 0                              | 9                              |
| credits_amount_mtd               | DOUBLE        |              0    |           81044 | 0.0                            | 49846.93                       |
| debits_count_mtd                 | BIGINT        |              0    |              44 | 0                              | 60                             |
| debits_amount_mtd                | DOUBLE        |              0    |           73984 | 0.0                            | 49741.96                       |
| payroll_deposit_flag             | BOOLEAN       |              0    |               2 | false                          | true                           |
| payroll_descriptor_raw           | VARCHAR       |             62.34 |            4413 | ALGONQUIN ACCOUNT PAIE         | WILDROSE TRUCKING PAY          |
| payroll_frequency_detected       | VARCHAR       |             62.34 |               4 | biweekly                       | weekly                         |
| last_payroll_date                | DATE          |             63.73 |             671 | 2016-11-04                     | 2026-09-25                     |
| last_payroll_amount              | DOUBLE        |             63.73 |           53922 | 77.96                          | 40404.25                       |
| expected_next_payroll_date       | DATE          |             63.73 |            1083 | 2016-11-11                     | 2026-10-10                     |
| payroll_delay_days               | BIGINT        |             63.73 |             305 | 0                              | 400                            |
| payroll_avg_amount_3m            | DOUBLE        |             65.32 |           55182 | 86.76                          | 40428.14                       |
| payroll_amount_change_pct        | DOUBLE        |             65.32 |            3738 | -0.4885                        | 0.2511                         |
| payroll_count_mtd                | BIGINT        |              0    |               6 | 0                              | 5                              |
| ei_deposit_flag                  | BOOLEAN       |              0    |               2 | false                          | true                           |
| ei_first_deposit_date            | DATE          |             96.8  |             617 | 2017-01-03                     | 2026-09-28                     |
| cpp_oas_deposit_flag             | BOOLEAN       |              0    |               2 | false                          | true                           |
| ccb_deposit_flag                 | BOOLEAN       |              0    |               2 | false                          | true                           |
| gst_hst_credit_flag              | BOOLEAN       |              0    |               2 | false                          | true                           |
| provincial_benefit_flag          | BOOLEAN       |              0    |               2 | false                          | true                           |
| etransfer_in_count_mtd           | BIGINT        |              0    |               4 | 0                              | 3                              |
| etransfer_in_amount_mtd          | DOUBLE        |              0    |             187 | 0.0                            | 24048.21                       |
| etransfer_out_count_mtd          | BIGINT        |              0    |               5 | 0                              | 4                              |
| etransfer_out_amount_mtd         | DOUBLE        |              0    |           47927 | 0.0                            | 799.96                         |
| bill_payment_count_mtd           | BIGINT        |              0    |              10 | 0                              | 8                              |
| bill_payment_amount_mtd          | DOUBLE        |              0    |           55733 | 0.0                            | 16009.4                        |
| pad_debit_count_mtd              | BIGINT        |              0    |               7 | 0                              | 6                              |
| other_lender_payment_count_mtd   | BIGINT        |              0    |               3 | 0                              | 2                              |
| other_lender_payment_amount_mtd  | DOUBLE        |              0    |           32042 | 0.0                            | 399.99                         |
| high_cost_lender_txn_flag        | BOOLEAN       |              0    |               2 | false                          | true                           |
| atm_withdrawal_amount_mtd        | BIGINT        |              0    |             230 | 0                              | 4130                           |
| pos_debit_amount_mtd             | DOUBLE        |              0    |           59781 | 0.0                            | 15083.7                        |
| essential_spend_amount_mtd       | DOUBLE        |              0    |           67586 | 0.0                            | 28592.52                       |
| discretionary_spend_amount_mtd   | DOUBLE        |              0    |           34775 | 0.0                            | 4623.89                        |
| rent_payment_detected_flag       | BOOLEAN       |              0    |               2 | false                          | true                           |
| net_cash_flow_mtd                | DOUBLE        |              0    |           66653 | -11006.54                      | 9018.82                        |
| cash_flow_volatility_6m          | DOUBLE        |              0    |           29486 | 0.0                            | 254.2759                       |
| income_to_debt_service_ratio_est | DOUBLE        |             39.03 |          109623 | 0.0                            | 57955.5                        |
| garnishment_flag                 | BOOLEAN       |              0    |               2 | false                          | true                           |
| estatement_flag                  | BOOLEAN       |              0    |               2 | false                          | true                           |
| dormant_days                     | BIGINT        |              0    |             610 | 0                              | 900                            |
| month_end_balance_m01            | DOUBLE        |              0    |          176473 | -5225.44                       | 5961.3                         |
| month_end_balance_m02            | DOUBLE        |              0    |          133790 | -5232.8                        | 7181.66                        |
| month_end_balance_m03            | DOUBLE        |              0    |          189224 | -5220.23                       | 7491.31                        |
| month_end_balance_m04            | DOUBLE        |              0    |          146888 | -5244.11                       | 8616.93                        |
| month_end_balance_m05            | DOUBLE        |              0    |          132332 | -5239.79                       | 9967.44                        |
| month_end_balance_m06            | DOUBLE        |              0    |          176876 | -5246.52                       | 11349.57                       |
| month_end_balance_m07            | DOUBLE        |              0    |          158880 | -5229.56                       | 12661.97                       |
| month_end_balance_m08            | DOUBLE        |              0    |          181423 | -5167.85                       | 14511.86                       |
| month_end_balance_m09            | DOUBLE        |              0    |          172619 | -5188.43                       | 15103.84                       |
| month_end_balance_m10            | DOUBLE        |              0    |          133197 | -5168.15                       | 16999.44                       |
| month_end_balance_m11            | DOUBLE        |              0    |          167502 | -5240.42                       | 19657.71                       |
| month_end_balance_m12            | DOUBLE        |              0    |          141520 | -5148.22                       | 20018.12                       |
| payroll_amount_m01               | DOUBLE        |              0    |           60810 | 0.0                            | 49337.44                       |
| payroll_amount_m02               | DOUBLE        |              0    |           57424 | 0.0                            | 75237.33                       |
| payroll_amount_m03               | DOUBLE        |              0    |           77984 | 0.0                            | 49045.28                       |
| payroll_amount_m04               | DOUBLE        |              0    |           89192 | 0.0                            | 72834.83                       |
| payroll_amount_m05               | DOUBLE        |              0    |           52661 | 0.0                            | 49158.57                       |
| payroll_amount_m06               | DOUBLE        |              0    |           74590 | 0.0                            | 49145.45                       |
| payroll_amount_m07               | DOUBLE        |              0    |           74418 | 0.0                            | 50181.97                       |
| payroll_amount_m08               | DOUBLE        |              0    |           68763 | 0.0                            | 75860.17                       |
| payroll_amount_m09               | DOUBLE        |              0    |           66742 | 0.0                            | 51090.23                       |
| payroll_amount_m10               | DOUBLE        |              0    |           77640 | 0.0                            | 57522.02                       |
| payroll_amount_m11               | DOUBLE        |              0    |           62342 | 0.0                            | 72755.15                       |
| payroll_amount_m12               | DOUBLE        |              0    |           66748 | 0.0                            | 50881.42                       |
| net_cash_flow_m01                | DOUBLE        |              0    |           54911 | -12293.76                      | 9745.11                        |
| net_cash_flow_m02                | DOUBLE        |              0    |           62764 | -12619.59                      | 11239.8                        |
| net_cash_flow_m03                | DOUBLE        |              0    |           70362 | -13301.73                      | 10206.39                       |
| net_cash_flow_m04                | DOUBLE        |              0    |           65675 | -13944.49                      | 10059.96                       |
| net_cash_flow_m05                | DOUBLE        |              0    |           65145 | -12851.1                       | 9879.6                         |
| net_cash_flow_m06                | DOUBLE        |              0    |           64237 | -9926.93                       | 13568.62                       |
| net_cash_flow_m07                | DOUBLE        |              0    |           65063 | -16187.01                      | 10449.62                       |
| net_cash_flow_m08                | DOUBLE        |              0    |           64718 | -15184.29                      | 10179.71                       |
| net_cash_flow_m09                | DOUBLE        |              0    |           56285 | -9590.82                       | 17810.18                       |
| net_cash_flow_m10                | DOUBLE        |              0    |           63438 | -20851.81                      | 20043.69                       |
| net_cash_flow_m11                | DOUBLE        |              0    |           77785 | -22531.26                      | 10757.06                       |
| net_cash_flow_m12                | DOUBLE        |              0    |           66107 | -10404.48                      | 8029.14                        |
| nsf_count_m01                    | BIGINT        |              0    |               9 | 0                              | 7                              |
| nsf_count_m02                    | BIGINT        |              0    |               7 | 0                              | 6                              |
| nsf_count_m03                    | BIGINT        |              0    |               6 | 0                              | 5                              |
| nsf_count_m04                    | BIGINT        |              0    |               7 | 0                              | 6                              |
| nsf_count_m05                    | BIGINT        |              0    |               7 | 0                              | 6                              |
| src_system                       | VARCHAR       |              0    |               1 | CORE                           | CORE                           |
| batch_id                         | VARCHAR       |              0    |            2720 | DDA_20170405_01                | DDA_20260928_01                |
| extract_ts                       | TIMESTAMP     |              0    |            3840 | 2017-04-05 04:05:00            | 2026-09-28 04:05:00            |
| src_file_name                    | VARCHAR       |              0    |            3878 | dda_snap_20170405.csv          | dda_snap_20260928.csv          |
| record_hash                      | VARCHAR       |              0    |          258698 | 00004209eb5ed6d34eaac6e956093f | ffffa63b8f5c6f7a8c6e90f8373f7f |
| credits_amount_m01               | DOUBLE        |              0    |          107859 | 0.0                            | 66973.41                       |
| credits_amount_m02               | DOUBLE        |              0    |           92826 | 0.0                            | 75237.33                       |
| credits_amount_m03               | DOUBLE        |              0    |          116578 | 0.0                            | 69249.09                       |
| credits_amount_m04               | DOUBLE        |              0    |           95234 | 0.0                            | 72834.83                       |
| credits_amount_m05               | DOUBLE        |              0    |          112090 | 0.0                            | 56942.5                        |
| credits_amount_m06               | DOUBLE        |              0    |           85936 | 0.0                            | 49145.45                       |
| credits_amount_m07               | DOUBLE        |              0    |          111605 | 0.0                            | 51196.8                        |
| credits_amount_m08               | DOUBLE        |              0    |          102752 | 0.0                            | 81795.34                       |
| credits_amount_m09               | DOUBLE        |              0    |           89099 | 0.0                            | 83290.17                       |
| credits_amount_m10               | DOUBLE        |              0    |          124524 | 0.0                            | 69285.99                       |
| credits_amount_m11               | DOUBLE        |              0    |           86165 | 0.0                            | 72755.15                       |
| credits_amount_m12               | DOUBLE        |              0    |           89398 | 0.0                            | 72616.37                       |
| debits_amount_m01                | DOUBLE        |              0    |          118336 | 0.0                            | 66911.76                       |
| debits_amount_m02                | DOUBLE        |              0    |           94502 | 0.0                            | 74972.08                       |
| debits_amount_m03                | DOUBLE        |              0    |          119156 | 0.0                            | 69226.35                       |
| debits_amount_m04                | DOUBLE        |              0    |          126024 | 0.0                            | 73156.73                       |
| debits_amount_m05                | DOUBLE        |              0    |           98868 | 0.0                            | 57059.82                       |
| debits_amount_m06                | DOUBLE        |              0    |          102115 | 0.0                            | 49308.64                       |
| debits_amount_m07                | DOUBLE        |              0    |          107292 | 0.0                            | 50920.94                       |
| debits_amount_m08                | DOUBLE        |              0    |          117676 | 0.0                            | 82185.01                       |
| debits_amount_m09                | DOUBLE        |              0    |           92416 | 0.0                            | 83297.13                       |
| debits_amount_m10                | DOUBLE        |              0    |           99195 | 0.0                            | 69052.02                       |
| debits_amount_m11                | DOUBLE        |              0    |          113386 | 0.0                            | 73071.38                       |
| debits_amount_m12                | DOUBLE        |              0    |          101606 | 0.0                            | 72993.8                        |
| overdraft_dpd                    | BIGINT        |             99.02 |             201 | 1                              | 181                            |
| overdraft_dpd_bucket             | VARCHAR       |             98.94 |               7 | 1-30                           | 91-120                         |

## external (1,000,000 rows)

| column_name                       | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:----------------------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| bureau_request_id                 | VARCHAR       |              0    |          189990 | EQ-201703-0002761749           | TU-202609-0099994493           |
| bureau_name                       | VARCHAR       |              0    |               2 | bureau_E                       | bureau_T                       |
| pull_date                         | DATE          |              0    |             117 | 2017-03-15                     | 2026-09-15                     |
| pull_type                         | VARCHAR       |              0    |               2 | account_review                 | application                    |
| bank_subject_ref                  | VARCHAR       |              0    |          233506 | 0001000771                     | 0099999248                     |
| bureau_file_number                | VARCHAR       |              1.96 |          198321 | 1000018365                     | 9999817215                     |
| hit_status                        | VARCHAR       |              0    |               2 | hit                            | thin_file                      |
| subject_name_reported             | VARCHAR       |              3.9  |          206105 | ABBOTT, ADRIANA GINA           | ZUNIGA, XAVIER TOMMY           |
| subject_dob_reported              | DATE          |              3.93 |           19044 | 1940-10-15                     | 2008-09-27                     |
| subject_address_reported          | VARCHAR       |              4.87 |          173351 | 1 BAY ST, HAMILTON ON L8T6X7   | 9999 WILSON ST, MISSISSAUGA ON |
| address_mismatch_flag             | BOOLEAN       |              0    |               2 | false                          | true                           |
| risk_score                        | BIGINT        |              7.13 |             535 | 300                            | 850                            |
| risk_score_model                  | VARCHAR       |              0    |               1 | RS-3.0                         | RS-3.0                         |
| risk_score_prev_3m                | BIGINT        |             10.01 |             532 | 310                            | 850                            |
| risk_score_delta_90d              | BIGINT        |             10.04 |              70 | -60                            | 15                             |
| score_reason_code_1               | VARCHAR       |              3    |              37 | R01                            | R39                            |
| score_reason_code_2               | VARCHAR       |              4.9  |              37 | R01                            | R39                            |
| score_reason_code_3               | VARCHAR       |              8.09 |              37 | R01                            | R39                            |
| score_reason_code_4               | VARCHAR       |             11.91 |              37 | R01                            | R39                            |
| bankruptcy_score                  | BIGINT        |              8.14 |             832 | 1                              | 820                            |
| file_since_date                   | DATE          |              1.96 |           14442 | 1986-11-01                     | 2026-09-20                     |
| months_since_oldest_trade         | BIGINT        |              1.96 |             499 | 1                              | 479                            |
| months_since_newest_trade         | BIGINT        |              1.96 |              41 | 1                              | 40                             |
| fraud_alert_flag                  | BOOLEAN       |              0    |               2 | false                          | true                           |
| file_freeze_flag                  | BOOLEAN       |              0    |               2 | false                          | true                           |
| deceased_indicator                | BOOLEAN       |              0    |               2 | false                          | true                           |
| consumer_statement_flag           | BOOLEAN       |              0    |               2 | false                          | true                           |
| bankruptcy_on_file_flag           | BOOLEAN       |              0    |               2 | false                          | true                           |
| consumer_proposal_on_file_flag    | BOOLEAN       |              0    |               2 | false                          | true                           |
| public_record_date                | DATE          |             98.88 |            1009 | 2017-02-13                     | 2026-09-15                     |
| judgment_count                    | BIGINT        |              0    |               5 | 0                              | 4                              |
| collection_items_count            | BIGINT        |              0    |               6 | 0                              | 5                              |
| collection_items_balance          | DOUBLE        |              0    |           12682 | 0.0                            | 17185.84                       |
| registered_items_count            | BIGINT        |              0    |               5 | 0                              | 4                              |
| inquiries_hard_3m                 | BIGINT        |              0    |              26 | 0                              | 25                             |
| inquiries_hard_6m                 | BIGINT        |              0    |              13 | 0                              | 11                             |
| inquiries_hard_12m                | BIGINT        |              0    |              13 | 0                              | 11                             |
| inquiries_soft_12m                | BIGINT        |              0    |              27 | 0                              | 26                             |
| months_since_last_inquiry         | BIGINT        |              4.94 |              26 | 0                              | 24                             |
| total_monthly_obligations         | DOUBLE        |              3    |          106668 | 0.23                           | 20286.12                       |
| total_balance_all_trades          | DOUBLE        |              0    |          176755 | 7.65                           | 1375483.68                     |
| total_limit_revolving             | BIGINT        |              0    |            1294 | 700                            | 411700                         |
| total_balance_revolving           | DOUBLE        |              0    |          196821 | 5.37                           | 182299.25                      |
| revolving_utilisation             | DOUBLE        |              0    |            9216 | 0.0004                         | 1.2                            |
| off_us_revolving_balance          | DOUBLE        |              0    |          150564 | 1.19                           | 140320.33                      |
| off_us_delinquent_trades          | BIGINT        |              0    |               9 | 0                              | 7                              |
| mortgage_trades_count             | BIGINT        |              0    |               2 | 0                              | 1                              |
| mortgage_balance_total            | DOUBLE        |              0    |           28293 | 0.0                            | 1356585.36                     |
| heloc_trades_count                | BIGINT        |              0    |               2 | 0                              | 1                              |
| high_cost_lender_trades_count     | BIGINT        |              0    |               6 | 0                              | 5                              |
| bnpl_trades_count                 | BIGINT        |              0    |               9 | 0                              | 7                              |
| telecom_trades_delinquent         | BIGINT        |              0    |               6 | 0                              | 5                              |
| new_trades_6m                     | BIGINT        |              0    |               7 | 0                              | 6                              |
| closed_trades_12m                 | BIGINT        |              0    |               6 | 0                              | 5                              |
| revolving_trades_open             | BIGINT        |              0    |              13 | 1                              | 12                             |
| revolving_worst_rating_current    | VARCHAR       |              0    |               5 | R1                             | R9                             |
| revolving_worst_rating_24m        | VARCHAR       |              0    |               5 | R1                             | R9                             |
| revolving_count_r2_12m            | BIGINT        |              0    |               5 | 0                              | 4                              |
| revolving_count_r2_24m            | BIGINT        |              0    |               7 | 0                              | 6                              |
| revolving_count_r3_12m            | BIGINT        |              0    |               5 | 0                              | 4                              |
| revolving_count_r3_24m            | BIGINT        |              0    |               7 | 0                              | 6                              |
| revolving_count_r4_12m            | BIGINT        |              0    |               5 | 0                              | 4                              |
| revolving_count_r4_24m            | BIGINT        |              0    |               7 | 0                              | 6                              |
| revolving_count_r5_12m            | BIGINT        |              0    |               5 | 0                              | 4                              |
| revolving_count_r5_24m            | BIGINT        |              0    |               7 | 0                              | 6                              |
| revolving_count_r9_12m            | BIGINT        |              0    |               1 | 0                              | 0                              |
| revolving_count_r9_24m            | BIGINT        |              0    |               1 | 0                              | 0                              |
| revolving_balance_total           | DOUBLE        |              0    |          196821 | 5.37                           | 182299.25                      |
| revolving_past_due_total          | DOUBLE        |              0    |           15799 | 0.0                            | 20587.66                       |
| instalment_trades_open            | BIGINT        |              0    |              10 | 0                              | 8                              |
| instalment_worst_rating_current   | VARCHAR       |              0    |               4 | I1                             | I4                             |
| instalment_worst_rating_24m       | VARCHAR       |              0    |               4 | I1                             | I4                             |
| instalment_count_i2_12m           | BIGINT        |              0    |               4 | 0                              | 3                              |
| instalment_count_i2_24m           | BIGINT        |              0    |               6 | 0                              | 5                              |
| instalment_count_i3_12m           | BIGINT        |              0    |               4 | 0                              | 3                              |
| instalment_count_i3_24m           | BIGINT        |              0    |               6 | 0                              | 5                              |
| instalment_count_i4_12m           | BIGINT        |              0    |               4 | 0                              | 3                              |
| instalment_count_i4_24m           | BIGINT        |              0    |               6 | 0                              | 5                              |
| instalment_count_i5_12m           | BIGINT        |              0    |               4 | 0                              | 3                              |
| instalment_count_i5_24m           | BIGINT        |              0    |               6 | 0                              | 5                              |
| instalment_count_i9_12m           | BIGINT        |              0    |               1 | 0                              | 0                              |
| instalment_count_i9_24m           | BIGINT        |              0    |               1 | 0                              | 0                              |
| instalment_balance_total          | DOUBLE        |              0    |          108601 | 0.0                            | 805702.55                      |
| instalment_past_due_total         | DOUBLE        |              0    |           12475 | 0.0                            | 19490.72                       |
| open_trades_open                  | BIGINT        |              0    |               9 | 0                              | 7                              |
| open_worst_rating_current         | VARCHAR       |              0    |               2 | O1                             | O2                             |
| open_worst_rating_24m             | VARCHAR       |              0    |               2 | O1                             | O2                             |
| open_count_o2_12m                 | BIGINT        |              0    |               3 | 0                              | 2                              |
| open_count_o2_24m                 | BIGINT        |              0    |               3 | 0                              | 2                              |
| open_count_o3_12m                 | BIGINT        |              0    |               1 | 0                              | 0                              |
| open_count_o3_24m                 | BIGINT        |              0    |               1 | 0                              | 0                              |
| open_count_o4_12m                 | BIGINT        |              0    |               1 | 0                              | 0                              |
| open_count_o4_24m                 | BIGINT        |              0    |               1 | 0                              | 0                              |
| open_count_o5_12m                 | BIGINT        |              0    |               1 | 0                              | 0                              |
| open_count_o5_24m                 | BIGINT        |              0    |               1 | 0                              | 0                              |
| open_count_o9_12m                 | BIGINT        |              0    |               1 | 0                              | 0                              |
| open_count_o9_24m                 | BIGINT        |              0    |               1 | 0                              | 0                              |
| open_balance_total                | DOUBLE        |              0    |           76830 | 8.32                           | 11105.65                       |
| open_past_due_total               | DOUBLE        |              0    |            9874 | 0.0                            | 1065.59                        |
| src_system                        | VARCHAR       |              0    |               1 | BUREAU                         | BUREAU                         |
| batch_id                          | VARCHAR       |              0    |             129 | BUR_201703                     | BUR_202609                     |
| file_received_ts                  | TIMESTAMP     |              0    |             107 | 2017-03-16 06:00:00            | 2026-09-16 06:00:00            |
| src_file_name                     | VARCHAR       |              0    |             102 | bureau_refresh_201703.csv      | bureau_refresh_202609.csv      |
| record_hash                       | VARCHAR       |              0    |          247082 | 00009679e577950b68dff774cee515 | ffffe5cf15ae5499430000e21abc80 |
| risk_score_m01                    | BIGINT        |             83.85 |             535 | 300                            | 850                            |
| risk_score_m02                    | BIGINT        |             83.85 |             535 | 300                            | 850                            |
| risk_score_m03                    | BIGINT        |             83.85 |             535 | 302                            | 850                            |
| risk_score_m04                    | BIGINT        |             83.85 |             532 | 300                            | 850                            |
| risk_score_m05                    | BIGINT        |             83.85 |             535 | 300                            | 850                            |
| risk_score_m06                    | BIGINT        |             83.85 |             532 | 301                            | 850                            |
| risk_score_m07                    | BIGINT        |             83.85 |             535 | 300                            | 850                            |
| risk_score_m08                    | BIGINT        |             83.85 |             532 | 300                            | 850                            |
| risk_score_m09                    | BIGINT        |             83.85 |             532 | 304                            | 850                            |
| risk_score_m10                    | BIGINT        |             83.85 |             532 | 302                            | 850                            |
| risk_score_m11                    | BIGINT        |             83.85 |             532 | 305                            | 850                            |
| risk_score_m12                    | BIGINT        |             83.85 |             532 | 306                            | 850                            |
| months_since_last_delinquency_any | BIGINT        |             63.15 |              57 | 0                              | 60                             |
| avg_age_of_trades_months          | BIGINT        |              1.96 |             260 | 1                              | 239                            |
| highest_revolving_limit           | BIGINT        |              0    |             963 | 300                            | 297100                         |
| revolving_util_trend_6m           | DOUBLE        |              0    |            4507 | -0.2343                        | 0.3                            |
| balance_growth_6m_pct             | DOUBLE        |              0    |            6433 | -0.3386                        | 0.4                            |
| payment_to_balance_ratio_3m       | DOUBLE        |              0    |            4438 | 0.0                            | 0.4                            |

## geo_reference (656 rows)

| column_name        | column_type   |   null_percentage |   approx_unique | min                   | max                   |
|:-------------------|:--------------|------------------:|----------------:|:----------------------|:----------------------|
| fsa                | VARCHAR       |              0    |             631 | A0B                   | Y1A                   |
| province_code      | VARCHAR       |              0    |              12 | AB                    | YT                    |
| city               | VARCHAR       |              0    |              93 | Abbotsford            | Yellowknife           |
| cma_name           | VARCHAR       |             15.09 |              48 | Abbotsford - Mission  | Yellowknife           |
| economic_region    | VARCHAR       |              0    |              53 | Annapolis Valley      | Yukon                 |
| common_region_name | VARCHAR       |              0    |              58 | Acadian Peninsula     | Yellowknife           |
| broad_region       | VARCHAR       |              0    |              50 | Avalon Peninsula      | Yukon                 |
| urban_rural        | VARCHAR       |              0    |               2 | rural                 | urban                 |
| time_zone          | VARCHAR       |              0    |               9 | America/Edmonton      | America/Yellowknife   |
| area_codes         | VARCHAR       |              0    |              24 | ["204", "431", "584"] | ["905", "289", "365"] |
| population_weight  | DOUBLE        |              0    |             578 | 3.2e-05               | 0.011505              |
| fsa_income_index   | DOUBLE        |              0    |             404 | 54.8                  | 224.8                 |
| majority_language  | VARCHAR       |              0    |               3 | EN                    | bilingual             |
| centroid_lat       | DOUBLE        |              0    |             759 | 42.22338              | 63.71227              |
| centroid_lon       | DOUBLE        |              0    |             788 | -135.04159            | -52.57607             |

## hardship_programs (18 rows)

| column_name               | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:--------------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| program_id                | VARCHAR       |              0    |              11 | HP-CARD-FPP                    | HP-SETTLE                      |
| version                   | VARCHAR       |              0    |               2 | 2025.1                         | 2026.1                         |
| program_name              | VARCHAR       |              0    |              11 | 3-month reduced payment        | Term extension                 |
| product_types             | VARCHAR       |              0    |               6 | ["card", "loc", "personal_loan | ["personal_loan", "auto_loan", |
| policy_section            | VARCHAR       |              0    |               2 | §4.2                           | §4.4                           |
| description               | VARCHAR       |              0    |              10 | Debt management plan through a | Skip one minimum payment; once |
| min_hardship_level        | VARCHAR       |              0    |               2 | clear                          | possible                       |
| max_dpd                   | BIGINT        |              0    |               6 | 60                             | 999                            |
| min_months_on_book        | BIGINT        |              0    |               3 | 0                              | 12                             |
| max_uses_12m              | BIGINT        |              0    |               1 | 1                              | 1                              |
| excludes_insolvency       | BOOLEAN       |              0    |               2 | false                          | true                           |
| excludes_broken_plan_90d  | BOOLEAN       |              0    |               2 | false                          | true                           |
| requires_income_evidence  | BOOLEAN       |              0    |               2 | false                          | true                           |
| payment_reduction_pct     | DOUBLE        |             16.67 |               5 | 0.25                           | 1.0                            |
| rate_override             | DOUBLE        |             72.22 |               1 | 0.0                            | 0.0999                         |
| duration_months           | BIGINT        |              0    |               5 | 1                              | 48                             |
| term_extension_max_months | BIGINT        |             88.89 |               1 | 12                             | 12                             |
| fees_waived_flag          | BOOLEAN       |              0    |               2 | false                          | true                           |
| approver_level            | VARCHAR       |              0    |               3 | agent                          | team_lead                      |
| effective_from            | DATE          |              0    |               2 | 2025-03-01                     | 2026-03-01                     |
| effective_to              | DATE          |              0    |               2 | 2026-02-28                     | 9999-12-31                     |

## loan_accounts (404,500 rows)

| column_name              | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:-------------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| loan_id                  | VARCHAR       |              0    |          200629 | L-1000081                      | L-9999998                      |
| snapshot_date            | DATE          |              0    |            3370 | 2017-04-05                     | 2026-09-28                     |
| snapshot_type            | VARCHAR       |              0    |               1 | daily                          | month_end                      |
| src_customer_ref         | VARCHAR       |              0    |          219168 | B00000145                      | B99999738                      |
| borrower_name_raw        | VARCHAR       |              0    |          159272 | ABBOTT BRYCE                   | Étienne Vincent                |
| borrower_dob_raw         | VARCHAR       |              0.99 |           26082 | 1940/10/15                     | 2008/09/27                     |
| borrower_phone_raw       | VARCHAR       |              2    |          164219 | +1 (204) 200 3711              | +1 (905) 999 8893              |
| borrower_postal_raw      | VARCHAR       |              1.03 |          170369 | A0B 0C3                        | Y1A 9Z8                        |
| co_borrower_flag         | BOOLEAN       |              0    |               2 | false                          | true                           |
| co_borrower_ref          | VARCHAR       |             82.85 |           44229 | B00005760                      | B99998623                      |
| product_type             | VARCHAR       |              0    |               4 | auto_loan                      | unsecured_loc                  |
| product_code             | VARCHAR       |              0    |              13 | AUTO-60                        | PL-FIX-84                      |
| secured_flag             | BOOLEAN       |              0    |               2 | false                          | true                           |
| revolving_flag           | BOOLEAN       |              0    |               2 | false                          | true                           |
| loan_purpose             | VARCHAR       |              3    |               5 | debt_consolidation             | vehicle                        |
| origination_channel      | VARCHAR       |              0    |               4 | auto_dealer_indirect           | online                         |
| dealer_id                | VARCHAR       |             81.47 |            2693 | DLR-0100                       | DLR-2500                       |
| origination_date         | DATE          |              0    |            7616 | 1995-05-19                     | 2026-07-30                     |
| maturity_date            | DATE          |             24.88 |           15536 | 2017-08-06                     | 2051-07-30                     |
| original_amount          | BIGINT        |              0    |            1920 | 5000                           | 1500000                        |
| original_term_months     | BIGINT        |             24.88 |               7 | 24                             | 300                            |
| remaining_term_months    | BIGINT        |             24.88 |             339 | 3                              | 299                            |
| interest_rate            | DOUBLE        |              0    |            1428 | 0.039                          | 0.16                           |
| rate_type                | VARCHAR       |              0    |               2 | fixed                          | variable                       |
| prime_rate_at_snapshot   | DOUBLE        |              0    |              20 | 0.0245                         | 0.072                          |
| rate_spread_over_prime   | DOUBLE        |             69.97 |             753 | -0.008                         | 0.08                           |
| payment_frequency        | VARCHAR       |              0    |               4 | biweekly                       | weekly                         |
| scheduled_payment_amount | DOUBLE        |              0    |           99072 | 20.41                          | 9624.26                        |
| payment_due_day          | BIGINT        |             27.84 |              27 | 1                              | 31                             |
| next_due_date            | DATE          |              0    |            3385 | 2017-04-08                     | 2026-10-28                     |
| next_due_amount          | DOUBLE        |              0    |          107426 | 20.41                          | 33739.98                       |
| principal_balance        | DOUBLE        |              0    |          141108 | 0.0                            | 1494471.59                     |
| accrued_interest         | DOUBLE        |              0    |           47055 | 0.0                            | 21245.3                        |
| fees_outstanding         | BIGINT        |              0    |               4 | 0                              | 135                            |
| total_outstanding        | DOUBLE        |              0    |          160427 | 0.0                            | 1496264.96                     |
| payoff_amount            | DOUBLE        |              0    |          203452 | 0.0                            | 1496802.97                     |
| available_to_draw        | DOUBLE        |             75.12 |           39759 | 0.0                            | 35000.0                        |
| loc_utilisation          | DOUBLE        |             75.12 |            8750 | 0.0                            | 0.98                           |
| interest_only_min_flag   | BOOLEAN       |             75.12 |               2 | false                          | true                           |
| past_due_amount          | DOUBLE        |              0    |           25705 | 0.0                            | 28116.65                       |
| missed_payments_count    | BIGINT        |              0    |              27 | 0                              | 26                             |
| dpd                      | BIGINT        |              7.88 |             207 | 0                              | 181                            |
| dpd_bucket               | VARCHAR       |              0    |               9 | 1-30                           | current                        |
| delinquency_start_date   | DATE          |             85.72 |            1140 | 2016-12-06                     | 2026-09-27                     |
| last_payment_date        | DATE          |              0    |            3370 | 2016-11-04                     | 2026-09-28                     |
| last_payment_amount      | DOUBLE        |              0    |           97870 | 20.41                          | 32560.92                       |
| last_payment_method      | VARCHAR       |              0    |               3 | branch                         | pad                            |
| pad_enrolled             | BOOLEAN       |              0    |               2 | false                          | true                           |
| pad_source_account       | VARCHAR       |             25.13 |           61574 | CHQ-100029                     | EXTERNAL                       |
| pad_returned_count_90d   | BIGINT        |              0    |              16 | 0                              | 13                             |
| nsf_fee_count_12m        | BIGINT        |              0    |              34 | 0                              | 35                             |
| collateral_type          | VARCHAR       |              0    |               3 | none                           | vehicle                        |
| vehicle_year             | BIGINT        |             76.73 |              21 | 2008                           | 2026                           |
| vehicle_make             | VARCHAR       |             76.73 |              15 | Chevrolet                      | Volkswagen                     |
| vehicle_model            | VARCHAR       |             76.73 |              39 | 1500                           | Wrangler                       |
| vehicle_vin_hash         | VARCHAR       |             76.73 |           45105 | 000089bb06ac314c974b8511282740 | ffff6909287b4d032d7b242c78a541 |
| vehicle_value_estimate   | BIGINT        |             76.73 |             608 | 3200                           | 77000                          |
| loan_to_value            | DOUBLE        |             76.73 |           14370 | 0.0                            | 1.9192                         |
| ppsa_registration_flag   | BOOLEAN       |             76.73 |               1 | true                           | true                           |
| repossession_flag        | BOOLEAN       |              0    |               2 | false                          | true                           |
| repossession_date        | DATE          |             99.41 |             506 | 2017-05-30                     | 2026-09-28                     |
| creditor_insurance_flag  | BOOLEAN       |              0    |               2 | false                          | true                           |
| insurance_claim_status   | VARCHAR       |             80.02 |               4 | approved                       | submitted                      |
| deferral_count_life      | BIGINT        |              0    |               3 | 0                              | 2                              |
| last_deferral_date       | DATE          |             90.67 |            2708 | 2015-09-30                     | 2026-09-28                     |
| restructure_flag         | BOOLEAN       |              0    |               2 | false                          | true                           |
| restructure_date         | DATE          |             97.7  |             754 | 2016-09-24                     | 2026-09-28                     |
| restructure_type         | VARCHAR       |             97.7  |               2 | interest_only_period           | term_extension                 |
| amended_payment_amount   | DOUBLE        |             97.7  |            4022 | 15.03                          | 5264.47                        |
| hardship_program_flag    | BOOLEAN       |              0    |               2 | false                          | true                           |
| hardship_program_type    | VARCHAR       |             98.78 |               4 | debt_management_plan           | term_extension                 |
| hardship_start_date      | DATE          |             98.78 |             267 | 2022-12-11                     | 2026-09-28                     |
| hardship_end_date        | DATE          |             98.78 |             439 | 2026-09-29                     | 2030-09-07                     |
| chargeoff_flag           | BOOLEAN       |              0    |               2 | false                          | true                           |
| chargeoff_date           | DATE          |             99.47 |             851 | 2017-06-05                     | 2026-09-23                     |
| chargeoff_amount         | DOUBLE        |             99.47 |            1145 | 1207.72                        | 629571.78                      |
| recovery_amount_to_date  | DOUBLE        |             99.47 |             590 | 0.0                            | 471901.62                      |
| worst_dpd_12m            | BIGINT        |              0    |             207 | 0                              | 181                            |
| times_30dpd_12m          | BIGINT        |              0    |              10 | 0                              | 8                              |
| times_60dpd_12m          | BIGINT        |              0    |               7 | 0                              | 6                              |
| times_90dpd_12m          | BIGINT        |              0    |               5 | 0                              | 4                              |
| payment_history_24m      | VARCHAR       |              0    |            1383 | 000000000000000000000000       | 6543200000XXXXXXXXXXXXXX       |
| dpd_m01                  | BIGINT        |              0    |             207 | 0                              | 180                            |
| dpd_m02                  | BIGINT        |              0    |             159 | 0                              | 152                            |
| dpd_m03                  | BIGINT        |              2.32 |             121 | 0                              | 121                            |
| dpd_m04                  | BIGINT        |              5.08 |             103 | 0                              | 114                            |
| dpd_m05                  | BIGINT        |              8.05 |             112 | 0                              | 119                            |
| dpd_m06                  | BIGINT        |             11.07 |             112 | 0                              | 111                            |
| dpd_m07                  | BIGINT        |             14.06 |             102 | 0                              | 110                            |
| dpd_m08                  | BIGINT        |             16.68 |             111 | 0                              | 118                            |
| dpd_m09                  | BIGINT        |             19.39 |             111 | 0                              | 117                            |
| dpd_m10                  | BIGINT        |             21.97 |             108 | 0                              | 114                            |
| dpd_m11                  | BIGINT        |             24.4  |             112 | 0                              | 113                            |
| dpd_m12                  | BIGINT        |             26.69 |             101 | 0                              | 114                            |
| paid_amount_m01          | DOUBLE        |              0    |           93251 | 0.0                            | 23327.76                       |
| paid_amount_m02          | DOUBLE        |              0    |           99122 | 0.0                            | 17373.4                        |
| paid_amount_m03          | DOUBLE        |              2.32 |           87956 | 0.0                            | 17306.04                       |
| paid_amount_m04          | DOUBLE        |              5.08 |           97231 | 0.0                            | 22510.35                       |
| paid_amount_m05          | DOUBLE        |              8.05 |          101194 | 0.0                            | 32560.92                       |
| paid_amount_m06          | DOUBLE        |             11.07 |           87125 | 0.0                            | 31827.9                        |
| paid_amount_m07          | DOUBLE        |             14.06 |           91792 | 0.0                            | 19033.25                       |
| paid_amount_m08          | DOUBLE        |             16.68 |           98217 | 0.0                            | 17306.04                       |
| paid_amount_m09          | DOUBLE        |             19.39 |           95036 | 0.0                            | 28907.95                       |
| paid_amount_m10          | DOUBLE        |             21.97 |           82945 | 0.0                            | 19857.72                       |
| paid_amount_m11          | DOUBLE        |             24.4  |           90759 | 0.0                            | 15620.67                       |
| paid_amount_m12          | DOUBLE        |             26.69 |           76077 | 0.0                            | 21041.67                       |
| scheduled_amount_m01     | DOUBLE        |              0    |          108146 | 0.0                            | 11451.99                       |
| scheduled_amount_m02     | DOUBLE        |              0    |          103300 | 0.0                            | 13225.05                       |
| scheduled_amount_m03     | DOUBLE        |              2.32 |           99735 | 0.0                            | 9893.01                        |
| scheduled_amount_m04     | DOUBLE        |              5.08 |           98118 | 0.0                            | 12772.05                       |
| scheduled_amount_m05     | DOUBLE        |              8.05 |           95410 | 0.0                            | 12367.26                       |
| scheduled_amount_m06     | DOUBLE        |             11.07 |           95036 | 0.0                            | 11753.1                        |
| scheduled_amount_m07     | DOUBLE        |             14.06 |           95036 | 0.0                            | 10849.8                        |
| scheduled_amount_m08     | DOUBLE        |             16.68 |           97919 | 0.0                            | 13225.05                       |
| scheduled_amount_m09     | DOUBLE        |             19.39 |           85021 | 0.0                            | 11683.47                       |
| scheduled_amount_m10     | DOUBLE        |             21.97 |           96552 | 0.0                            | 11912.1                        |
| scheduled_amount_m11     | DOUBLE        |             24.4  |           85471 | 0.0                            | 12367.26                       |
| scheduled_amount_m12     | DOUBLE        |             26.69 |           78930 | 0.0                            | 10849.8                        |
| principal_balance_m01    | DOUBLE        |              0    |          166631 | 255.0                          | 1497621.54                     |
| principal_balance_m02    | DOUBLE        |              0    |          159568 | 255.0                          | 1500000.0                      |
| principal_balance_m03    | DOUBLE        |              2.32 |          186726 | 255.0                          | 1500000.0                      |
| principal_balance_m04    | DOUBLE        |              5.08 |          181306 | 255.0                          | 1494613.5                      |
| principal_balance_m05    | DOUBLE        |              8.05 |          156663 | 255.0                          | 1497852.25                     |
| principal_balance_m06    | DOUBLE        |             11.07 |          167938 | 255.0                          | 1500000.0                      |
| principal_balance_m07    | DOUBLE        |             14.06 |          135980 | 255.0                          | 1487618.22                     |
| principal_balance_m08    | DOUBLE        |             16.68 |          158134 | 255.0                          | 1490115.88                     |
| principal_balance_m09    | DOUBLE        |             19.39 |          185519 | 255.0                          | 1492602.83                     |
| principal_balance_m10    | DOUBLE        |             21.97 |          142641 | 255.0                          | 1495079.14                     |
| principal_balance_m11    | DOUBLE        |             24.4  |          148266 | 255.0                          | 1497544.85                     |
| principal_balance_m12    | DOUBLE        |             26.69 |          158587 | 255.0                          | 1500000.0                      |
| src_system               | VARCHAR       |              0    |               1 | LOANS                          | LOANS                          |
| batch_id                 | VARCHAR       |              0    |            3349 | LN_20170405_01                 | LN_20260928_01                 |
| extract_ts               | TIMESTAMP     |              0    |            3888 | 2017-04-05 03:40:00            | 2026-09-28 03:40:00            |
| src_file_name            | VARCHAR       |              0    |            3539 | ln_master_20170405.csv         | ln_master_20260928.csv         |
| record_hash              | VARCHAR       |              0    |          202389 | 00000a4b058cfda7986889e450a4ff | ffff346ed7836c7505a89990b30c69 |

## loan_instalments (14,832,472 rows)

| column_name         | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:--------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| loan_id             | VARCHAR       |              0    |          110458 | L-1000216                      | L-9999852                      |
| instalment_no       | BIGINT        |              0    |             737 | 1                              | 643                            |
| due_date            | DATE          |              0    |            4402 | 2013-05-04                     | 2026-10-28                     |
| due_amount          | DOUBLE        |              0    |           64973 | 20.41                          | 9748.31                        |
| principal_component | DOUBLE        |              0    |           60733 | 0.0                            | 6990.54                        |
| interest_component  | DOUBLE        |              0    |           70048 | 0.75                           | 7184.67                        |
| fee_component       | DOUBLE        |              0    |               1 | 0.0                            | 0.0                            |
| paid_amount         | DOUBLE        |              0    |           63774 | 0.0                            | 9748.31                        |
| paid_date           | DATE          |              3.96 |            4778 | 2013-05-03                     | 2026-09-28                     |
| days_late_when_paid | BIGINT        |             99.03 |             110 | 1                              | 120                            |
| instalment_status   | VARCHAR       |              0    |               5 | future                         | unpaid                         |
| pad_attempt_date    | DATE          |             26.95 |            4377 | 2013-05-04                     | 2026-09-28                     |
| pad_result          | VARCHAR       |             26.95 |               2 | nsf                            | success                        |
| pad_retry_date      | DATE          |             98.33 |            1001 | 2016-10-30                     | 2026-10-01                     |
| schedule_version    | BIGINT        |              0    |               2 | 1                              | 2                              |
| restructured_flag   | BOOLEAN       |              0    |               2 | false                          | true                           |
| deferred_flag       | BOOLEAN       |              0    |               1 | false                          | false                          |
| batch_id            | VARCHAR       |              0    |               1 | LN_INST_20260928               | LN_INST_20260928               |
| filename            | VARCHAR       |              0    |             264 | D:\iiith\maple_data\maple_coll | D:\iiith\maple_data\maple_coll |
| year                | BIGINT        |              0    |              16 | 2013                           | 2026                           |

## metric_definitions (15 rows)

| column_name         | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:--------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| metric_id           | VARCHAR       |                 0 |              16 | average_dpd                    | write_off_rate                 |
| metric_name         | VARCHAR       |                 0 |              17 | Amount collected               | Write-off rate                 |
| business_definition | VARCHAR       |                 0 |              16 | Average contact cost in CAD    | Total contact cost divided by  |
| formula             | VARCHAR       |                 0 |              17 | avg(current_dpd)               | sum(payments received on case  |
| grain               | VARCHAR       |                 0 |               5 | account                        | promise                        |
| time_basis          | VARCHAR       |                 0 |               9 | calendar month                 | snapshot date                  |
| default_filters     | VARCHAR       |                 0 |              13 | active accounts only           | right-party contacts only      |
| unit                | VARCHAR       |                 0 |               4 | cad                            | ratio                          |
| good_direction      | VARCHAR       |                 0 |               2 | down                           | up                             |
| synonyms            | VARCHAR       |                 0 |              17 | ["PTP kept rate", "promise kep | ["self-cure", "back to current |
| source_tables       | VARCHAR       |                 0 |               9 | ["account_monthly_snapshot", " | ["promises_to_pay"]            |
| example_question    | VARCHAR       |                 0 |              13 | Attempts per case by bucket?   | Write-offs in the last 12 mont |
| owner               | VARCHAR       |                 0 |               1 | Collections Analytics          | Collections Analytics          |
| certified_flag      | BOOLEAN       |                 0 |               1 | true                           | true                           |

## model_scores (1,718,841 rows)

| column_name               | column_type   |   null_percentage |   approx_unique | min                          | max                         |
|:--------------------------|:--------------|------------------:|----------------:|:-----------------------------|:----------------------------|
| score_id                  | VARCHAR       |              0    |          224798 | SC-20260630-0000001          | SC-20260928-9585982         |
| score_date                | DATE          |              0    |               4 | 2026-06-30                   | 2026-09-28                  |
| score_ts                  | TIMESTAMP     |              0    |               4 | 2026-06-30 06:00:00          | 2026-09-28 06:00:00         |
| model_name                | VARCHAR       |              0    |              11 | best_time_to_contact         | self_cure                   |
| model_version             | VARCHAR       |              0    |               9 | v0.9                         | v3.0                        |
| entity_type               | VARCHAR       |              0    |               5 | case                         | ptp                         |
| entity_id                 | VARCHAR       |              0    |          140315 | AAA-2567:Mon-Fri 18:00-20:00 | ZOZ-9840                    |
| crm_customer_id           | VARCHAR       |              0    |           94943 | AAA-2567                     | ZOZ-9840                    |
| case_id                   | VARCHAR       |              5.06 |           97845 | CS-2025-137742               | CS-2026-999995              |
| ptp_id                    | VARCHAR       |             96.19 |            6959 | PTP-0006876                  | PTP-9511669                 |
| score                     | DOUBLE        |              0    |           10075 | 0.0039                       | 1.0                         |
| score_band                | VARCHAR       |              0    |               4 | high                         | very_high                   |
| risk_grade                | BIGINT        |             78.62 |              11 | 1                            | 10                          |
| predicted_value           | DOUBLE        |             99.95 |              94 | 0.0                          | 16359.6                     |
| slot_label                | VARCHAR       |             66.57 |               7 | Mon-Fri 09:00-11:00          | sms                         |
| slot_rank                 | BIGINT        |             66.57 |               3 | 1                            | 3                           |
| answer_rate_estimate      | DOUBLE        |             57.09 |            9814 | 0.0039                       | 0.9934                      |
| top_reason_1              | VARCHAR       |              0    |               7 | bureau_score_delta_90d       | utilisation                 |
| top_reason_1_text         | VARCHAR       |              0    |             432 | 0 days past due              | Payroll deposit 9 days late |
| top_reason_1_contribution | DOUBLE        |              0    |            2140 | 0.02                         | 0.25                        |
| top_reason_2              | VARCHAR       |              4.93 |               7 | bureau_score_delta_90d       | utilisation                 |
| top_reason_2_text         | VARCHAR       |              4.93 |             432 | 0 days past due              | Payroll deposit 9 days late |
| top_reason_2_contribution | DOUBLE        |              4.93 |            1096 | 0.01                         | 0.125                       |
| top_reason_3              | VARCHAR       |              9.94 |               7 | bureau_score_delta_90d       | utilisation                 |
| top_reason_3_text         | VARCHAR       |              9.94 |             432 | 0 days past due              | Payroll deposit 9 days late |
| top_reason_3_contribution | DOUBLE        |              9.94 |             869 | 0.0067                       | 0.0833                      |
| features_snapshot_id      | VARCHAR       |              0    |          128637 | FV-20260630-G-0000086        | FV-20260928-G-0999982       |
| threshold_used            | DOUBLE        |             20.01 |               1 | 0.6                          | 0.6                         |
| recommended_action        | VARCHAR       |             60.1  |               6 | call_daytime                 | sms_payment_link            |
| model_owner               | VARCHAR       |              0    |               1 | Collections Analytics        | Collections Analytics       |
| auc_at_validation         | DOUBLE        |              0    |              10 | 0.62                         | 0.74                        |
| psi_last_month            | DOUBLE        |              0    |             365 | 0.0201                       | 0.27                        |
| uses_protected_attributes | BOOLEAN       |              0    |               1 | false                        | false                       |

## offers (40,767 rows)

| column_name             | column_type   |   null_percentage |   approx_unique | min                 | max                   |
|:------------------------|:--------------|------------------:|----------------:|:--------------------|:----------------------|
| offer_id                | VARCHAR       |              0    |           41901 | OF-0000001          | OF-9502089            |
| case_id                 | VARCHAR       |              0    |           47045 | CS-2016-141399      | CS-2026-999997        |
| account_id              | VARCHAR       |              0    |           42529 | C-100000            | L-9999611             |
| contact_id              | VARCHAR       |             27.87 |           34254 | CT-0000713          | CT-9626630            |
| agent_id                | VARCHAR       |             29.56 |             812 | AG-1003             | AG-9999               |
| program_id              | VARCHAR       |              0    |              11 | HP-CARD-FPP         | HP-SETTLE             |
| offer_ts                | TIMESTAMP     |              0    |           32267 | 2016-10-16 16:24:47 | 2026-10-22 13:53:20   |
| offered_by              | VARCHAR       |              0    |               4 | agent               | self_serve_app        |
| nba_recommended_flag    | BOOLEAN       |              0    |               2 | false               | true                  |
| eligibility_result      | VARCHAR       |              0    |               2 | eligible            | ineligible_overridden |
| proposed_payment_amount | DOUBLE        |              0    |           17318 | 25.0                | 27706.86              |
| duration_months         | BIGINT        |              0    |               5 | 1                   | 48                    |
| customer_response       | VARCHAR       |              0    |               4 | accepted            | no_response           |
| response_ts             | TIMESTAMP     |             23.11 |           37038 | 2016-10-19 10:58:47 | 2026-10-25 09:35:54   |
| decline_reason          | VARCHAR       |             72.85 |               5 | distrust            | will_pay_full         |
| plan_start_date         | DATE          |             49.74 |            2514 | 2016-10-22          | 2026-10-30            |
| plan_status             | VARCHAR       |             49.74 |               3 | active              | completed             |
| plan_payments_due       | BIGINT        |             49.74 |               5 | 1                   | 48                    |
| plan_payments_made      | BIGINT        |             49.74 |              45 | 0                   | 48                    |

## ops_events (6 rows)

| column_name            | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:-----------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| event_id               | VARCHAR       |              0    |               6 | DFI-0812                       | REL-0926                       |
| event_type             | VARCHAR       |              0    |               6 | app_outage                     | policy_change                  |
| system                 | VARCHAR       |              0    |               5 | Bureau file load               | Regional employer layoffs      |
| start_ts               | TIMESTAMP     |              0    |               5 | 2026-03-01 00:00:00            | 2026-09-26 00:00:00            |
| end_ts                 | TIMESTAMP     |              0    |               6 | 2026-03-01 00:00:00            | 2026-09-28 00:00:00            |
| severity               | VARCHAR       |              0    |               2 | sev2                           | sev3                           |
| description            | VARCHAR       |              0    |               6 | Auto-parts plant layoffs in Wi | contact_history column channel |
| affected_tables        | VARCHAR       |              0    |               6 | ["card_statements", "collectio | ["offers", "hardship_programs" |
| affected_customers_est | BIGINT        |              0    |               5 | 0                              | 35000                          |
| reference_doc_id       | VARCHAR       |             33.33 |               4 | IR-2026-0914                   | REL-0926                       |

## promises_to_pay (238,815 rows)

| column_name                 | column_type   |   null_percentage |   approx_unique | min                 | max                 |
|:----------------------------|:--------------|------------------:|----------------:|:--------------------|:--------------------|
| ptp_id                      | VARCHAR       |              0    |          218058 | PTP-0000002         | PTP-9511691         |
| case_id                     | VARCHAR       |              0    |          143753 | CS-2016-100672      | CS-2026-999985      |
| crm_customer_id             | VARCHAR       |              0    |           97427 | AAA-2758            | ZOZ-9840            |
| account_id                  | VARCHAR       |             28.69 |           99021 | C-100000            | L-9999611           |
| product                     | VARCHAR       |              0    |               7 | auto_loan           | personal_loan       |
| contact_id                  | VARCHAR       |              1.95 |          181519 | CT-0000054          | CT-9626678          |
| agent_id                    | VARCHAR       |             15.11 |             841 | AG-1003             | AG-9999             |
| ptp_channel                 | VARCHAR       |              0    |               5 | app                 | web                 |
| ptp_created_ts              | TIMESTAMP     |              0    |          202283 | 2016-10-05 13:22:46 | 2026-09-27 23:59:19 |
| ptp_amount                  | DOUBLE        |              0    |           39859 | 0.1                 | 27520.0             |
| ptp_due_date                | DATE          |              0    |            3858 | 2016-10-14          | 2026-10-18          |
| days_to_due_at_creation     | BIGINT        |              0    |              21 | 1                   | 21                  |
| ptp_type                    | VARCHAR       |              0    |               2 | instalment_1_of_n   | single              |
| ptp_sequence_in_case        | BIGINT        |              0    |               7 | 1                   | 7                   |
| prior_broken_ptp_count      | BIGINT        |              0    |               6 | 0                   | 5                   |
| overdue_at_creation         | DOUBLE        |              0    |           87497 | 0.51                | 28116.65            |
| ptp_to_overdue_ratio        | DOUBLE        |              0    |            9942 | 0.0005              | 1.0                 |
| dpd_at_creation             | BIGINT        |              0    |             207 | 0                   | 180                 |
| payment_method_promised     | VARCHAR       |             10.01 |               5 | branch              | pad                 |
| reminder_scheduled_flag     | BOOLEAN       |              0    |               2 | false               | true                |
| grace_days                  | BIGINT        |              0    |               1 | 2                   | 2                   |
| ptp_status                  | VARCHAR       |              0    |               5 | broken              | partially_kept      |
| status_ts                   | TIMESTAMP     |              0    |           32440 | 2016-10-06 12:00:00 | 2026-09-27 23:59:19 |
| amount_paid_against         | DOUBLE        |              0    |           37952 | 0.0                 | 28210.6             |
| paid_date                   | DATE          |             50.82 |            3838 | 2016-10-06          | 2026-09-25          |
| broken_reason_agent_coded   | VARCHAR       |             76.45 |               4 | dispute             | unreachable         |
| customer_stated_income_date | DATE          |             49.87 |            3858 | 2016-10-19          | 2026-10-18          |
| src_system                  | VARCHAR       |              0    |               1 | COLLX               | COLLX               |
| batch_id                    | VARCHAR       |              0    |               1 | COLLX_20260928      | COLLX_20260928      |

## qa_checklist (10 rows)

| column_name       | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| item_no           | BIGINT        |                 0 |              11 | 1                              | 10                             |
| item_code         | VARCHAR       |                 0 |              10 | agent_identified_self_and_purp | respectful_close_and_next_step |
| item_name         | VARCHAR       |                 0 |              10 | Agent identified self and purp | Respectful close and next step |
| pass_criteria     | VARCHAR       |                 0 |              11 | Agent gives name, Maple Bank a | When hardship is stated, the a |
| fail_examples     | VARCHAR       |                 0 |              11 | 'This will be reported as a cr | No recording notice            |
| weight            | BIGINT        |                 0 |               5 | 6                              | 18                             |
| critical_flag     | BOOLEAN       |                 0 |               2 | false                          | true                           |
| applies_when      | VARCHAR       |                 0 |               5 | All calls                      | Right-party contact            |
| evidence_required | BOOLEAN       |                 0 |               2 | false                          | true                           |
| version           | VARCHAR       |                 0 |               1 | QA-2026.2                      | QA-2026.2                      |

## reference_documents (19 rows)

| column_name          | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:---------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| doc_id               | VARCHAR       |              0    |              21 | DC-COLL-001                    | SCR-VUL-EN                     |
| doc_type             | VARCHAR       |              0    |              10 | call_script                    | release_note                   |
| title                | VARCHAR       |              0    |              20 | Collections Agent FAQ          | Vulnerable Customer Call Scrip |
| language             | VARCHAR       |              0    |               2 | EN                             | FR                             |
| version              | VARCHAR       |              0    |              10 | 1.0                            | 4.2                            |
| effective_date       | DATE          |              0    |              17 | 2023-05-01                     | 2026-09-26                     |
| superseded_by        | VARCHAR       |             89.47 |               2 | POL-COLL-004                   | SCR-MID-STD-EN                 |
| owner                | VARCHAR       |              0    |               7 | Collections Data Office        | Technology Risk                |
| section_ids          | VARCHAR       |              0    |              11 | ["Q1", "Q2", "Q3", "Q4"]       | ["§8.1", "§8.2"]               |
| file_path            | VARCHAR       |              0    |              16 | docs/data_contracts/DC-COLL-00 | docs/terms/HPT-2026_v2026.1_EN |
| page_count           | BIGINT        |              0    |               1 | 1                              | 1                              |
| word_count           | BIGINT        |              0    |              17 | 37                             | 486                            |
| applies_to_products  | VARCHAR       |              0    |               2 | ["card", "personal_loan", "aut | ["card"]                       |
| applies_to_provinces | VARCHAR       |              0    |               2 | ["ALL"]                        | ["QC"]                         |
| confidentiality      | VARCHAR       |              0    |               1 | internal                       | internal                       |
| related_incident_id  | VARCHAR       |             89.47 |               2 | INC-0914                       | INC-0923                       |
| related_table        | VARCHAR       |             94.74 |               1 | contact_history (channel -> ch | contact_history (channel -> ch |

## salary_credit_history (6,000,000 rows)

| column_name         | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:--------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| deposit_account_id  | VARCHAR       |              0    |          184722 | CHQ-100011                     | CHQ-999995                     |
| crm_customer_id     | VARCHAR       |              0    |          122941 | AAA-2071                       | ZOZ-9562                       |
| credit_month        | VARCHAR       |              0    |             136 | 2016-04                        | 2026-08                        |
| account_type        | VARCHAR       |              0    |               1 | chequing                       | chequing                       |
| employer_flag       | VARCHAR       |              0    |               2 | N                              | Y                              |
| credit_count        | BIGINT        |              0    |               6 | 0                              | 5                              |
| credit_amount_total | DOUBLE        |              0    |          101967 | 0.0                            | 60669.41                       |
| first_credit_date   | DATE          |             30.32 |            1071 | 2016-04-01                     | 2026-08-31                     |
| last_credit_date    | DATE          |             30.32 |             781 | 2016-04-22                     | 2026-08-31                     |
| gap_flag            | BOOLEAN       |              0    |               2 | false                          | true                           |
| filename            | VARCHAR       |              0    |             240 | D:\iiith\maple_data\maple_coll | D:\iiith\maple_data\maple_coll |
| year                | BIGINT        |              0    |              12 | 2016                           | 2026                           |

## transactions (12,401,924 rows)

| column_name             | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:------------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| txn_id                  | VARCHAR       |              0    |          188247 | TX-20160414-85536459           | TX-20260928-95567125           |
| account_id              | VARCHAR       |              0    |           86367 | CHQ-100011                     | CHQ-999984                     |
| account_type            | VARCHAR       |              0    |               1 | deposit                        | deposit                        |
| posting_date            | DATE          |              0    |            3226 | 2016-04-14                     | 2026-09-28                     |
| value_date              | DATE          |              0    |            3226 | 2016-04-14                     | 2026-09-28                     |
| txn_ts                  | TIMESTAMP     |              5.05 |          170379 | 2016-04-14 11:19:04            | 2026-09-28 23:40:19            |
| amount                  | DOUBLE        |              0    |           82251 | -24864.96                      | 39530.75                       |
| currency                | VARCHAR       |              0    |               1 | CAD                            | CAD                            |
| direction               | VARCHAR       |              0    |               2 | credit                         | debit                          |
| txn_type                | VARCHAR       |              0    |               9 | atm                            | pos_debit                      |
| channel                 | VARCHAR       |              0    |               4 | atm                            | pos                            |
| raw_description         | VARCHAR       |              0    |            4546 | ALGONQUIN ACCOUNT PAIE         | WILDROSE TRUCKING PAY          |
| counterparty_name_clean | VARCHAR       |             20.05 |           13970 | Algonquin Accounting Group     | Wildrose Trucking Inc.         |
| category                | VARCHAR       |              4.89 |              11 | benefits                       | utilities                      |
| benefit_type            | VARCHAR       |             93.32 |               4 | ccb                            | gst_hst_credit                 |
| is_payroll_flag         | BOOLEAN       |              0    |               2 | false                          | true                           |
| payroll_employer_key    | VARCHAR       |             87.41 |           16234 | EMP-00001                      | EMP-28571                      |
| target_account_id       | VARCHAR       |             90.56 |           19698 | C-100014                       | L-9998401                      |
| ptp_id_matched          | VARCHAR       |             99.9  |             202 | PTP-0001072                    | PTP-9508292                    |
| reversal_of_txn_id      | VARCHAR       |            100    |               0 | nan                            | nan                            |
| returned_flag           | BOOLEAN       |              0    |               1 | false                          | false                          |
| return_reason           | VARCHAR       |            100    |               0 | nan                            | nan                            |
| balance_after           | DOUBLE        |             30.02 |          130126 | -26080.2                       | 28705.51                       |
| batch_id                | VARCHAR       |              0    |             117 | TXN_201604                     | TXN_202609                     |
| filename                | VARCHAR       |              0    |             220 | D:\iiith\maple_data\maple_coll | D:\iiith\maple_data\maple_coll |
| year                    | BIGINT        |              0    |              12 | 2016                           | 2026                           |

## voice_samples (2,000 rows)

| column_name                | column_type   |   null_percentage |   approx_unique | min                            | max                            |
|:---------------------------|:--------------|------------------:|----------------:|:-------------------------------|:-------------------------------|
| voice_sample_id            | VARCHAR       |              0    |            2125 | VS-10000                       | VS-9511247                     |
| transcript_id              | VARCHAR       |              0    |            1956 | 10000                          | 9511247                        |
| contact_id                 | VARCHAR       |              0    |            2114 | CT-0012102                     | CT-9626483                     |
| file_path                  | VARCHAR       |              0    |            2496 | voice/VS-10000.wav             | voice/VS-9511247.wav           |
| file_size_bytes            | BIGINT        |              0    |             278 | 240044                         | 11968044                       |
| checksum_sha256            | VARCHAR       |              0    |            1964 | 005277776f3632a0d8581979af591e | ffeafbcc005a7e7f471923e8534e9e |
| audio_format               | VARCHAR       |              0    |               1 | wav_pcm_s16le                  | wav_pcm_s16le                  |
| original_codec             | VARCHAR       |              0    |               2 | g711_ulaw                      | opus_wideband                  |
| sample_rate_hz             | BIGINT        |              0    |               2 | 8000                           | 16000                          |
| bit_depth                  | BIGINT        |              0    |               1 | 16                             | 16                             |
| channels                   | BIGINT        |              0    |               2 | 1                              | 2                              |
| channel_map                | VARCHAR       |             29.65 |               1 | L=agent,R=customer             | L=agent,R=customer             |
| duration_sec               | BIGINT        |              0    |             164 | 15                             | 201                            |
| language                   | VARCHAR       |              0    |               1 | en-CA                          | en-CA                          |
| synthetic_voice_flag       | BOOLEAN       |              0    |               1 | true                           | true                           |
| agent_voice_id             | VARCHAR       |              0    |              12 | AGV-01                         | AGV-12                         |
| customer_voice_id          | VARCHAR       |              0    |              40 | CUV-01                         | CUV-40                         |
| customer_accent_region     | VARCHAR       |              0    |               6 | atlantic                       | southern_ontario               |
| agent_accent_region        | VARCHAR       |              0    |               4 | atlantic                       | southern_ontario               |
| speaking_rate_wpm_customer | BIGINT        |              0    |              31 | 134                            | 170                            |
| speaking_rate_wpm_agent    | BIGINT        |              0    |              11 | 138                            | 163                            |
| background_noise_type      | VARCHAR       |              0    |               7 | car                            | tv                             |
| snr_db                     | DOUBLE        |              0    |             236 | 5.0                            | 30.0                           |
| packet_loss_pct            | DOUBLE        |              0    |             234 | 0.0                            | 2.0                            |
| clipping_pct               | BIGINT        |              0    |               1 | 0                              | 0                              |
| dead_air_sec               | DOUBLE        |              0    |            1238 | 0.99                           | 93.45                          |
| hold_music_sec             | BIGINT        |              0    |               2 | 0                              | 30                             |
| customer_pitch_mean_hz     | DOUBLE        |              0    |              84 | 105.6                          | 233.9                          |
| customer_pitch_std_hz      | DOUBLE        |              0    |             264 | 15.0                           | 41.9                           |
| customer_energy_mean_db    | DOUBLE        |              0    |             219 | -120.0                         | -25.5                          |
| customer_pause_count       | BIGINT        |              0    |              13 | 0                              | 13                             |
| customer_filler_rate       | DOUBLE        |              0    |              52 | 0.01                           | 0.06                           |
| watermark_flag             | BOOLEAN       |              0    |               1 | true                           | true                           |
| consent_basis              | VARCHAR       |              0    |               1 | synthetic_tts_no_real_person   | synthetic_tts_no_real_person   |