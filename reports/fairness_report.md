# Fairness report
Scope: 83,677 open cases from gold.nba_recommendations.

**Methodology.** For each protected attribute we compute three metrics per group and the gap vs the population mean, flagging groups where the gap exceeds **5 percentage points**. Report-only; no live decisions are changed here. See CLAUDE.md §2 'Protected attributes' for the policy.

## gender_code

**Action distribution (% within group)**
| gender_code   |   call_best_time |   digital_nudge |   escalate |   hardship_referral |   no_contact |   payment_plan |
|---------------|------------------|-----------------|------------|---------------------|--------------|----------------|
| F             |             34.6 |            41.6 |        7.1 |                 6.8 |          8.7 |            1.1 |
| M             |             34.3 |            41.6 |        7.1 |                 7   |          8.7 |            1.2 |
| U             |             36.2 |            39.7 |        6.3 |                 6.5 |         10   |            1.4 |
| X             |             33.6 |            43.2 |        6.9 |                 5.3 |          9.3 |            1.6 |
| nan           |             37.1 |            40.4 |        6   |                 6.4 |          8.7 |            1.4 |

**Predicted cure (avg p_cure) — population mean 85.35%**
| gender_code   |     n |   pred_cure_pct |   gap_pp | verdict   |
|---------------|-------|-----------------|----------|-----------|
| F             | 40260 |           85.43 |     0.08 | ok        |
| M             | 40892 |           85.24 |    -0.11 | ok        |
| U             |   813 |           84.79 |    -0.56 | ok        |
| X             |   849 |           86.93 |     1.57 | ok        |
| nan           |   863 |           85.84 |     0.49 | ok        |

**vulnerability_signal rate — population 16.67%**
| gender_code   |     n |   vuln_pct |   gap_pp | verdict   |
|---------------|-------|------------|----------|-----------|
| F             | 40260 |      16.57 |    -0.09 | ok        |
| M             | 40892 |      16.89 |     0.22 | ok        |
| U             |   813 |      14.88 |    -1.78 | ok        |
| X             |   849 |      13.31 |    -3.36 | ok        |
| nan           |   863 |      15.41 |    -1.26 | ok        |

_Verdict for gender_code: all groups within the 5pp band on predicted cure._

## marital_status

**Action distribution (% within group)**
| marital_status   |   call_best_time |   digital_nudge |   escalate |   hardship_referral |   no_contact |   payment_plan |
|------------------|------------------|-----------------|------------|---------------------|--------------|----------------|
| common_law       |             34.6 |            41.4 |        6.7 |                 7.4 |          8.8 |            1.1 |
| divorced         |             34.4 |            41.5 |        7.1 |                 6.8 |          8.9 |            1.3 |
| married          |             34.1 |            41.5 |        7.5 |                 7.2 |          8.6 |            1.1 |
| separated        |             35.2 |            44.3 |        4.6 |                 5   |          9.8 |            1   |
| single           |             34.9 |            41   |        7.4 |                 6.9 |          8.5 |            1.3 |
| undisclosed      |             33.9 |            41.7 |        7.4 |                 7.8 |          8   |            1.3 |
| widowed          |             33.9 |            39.8 |        8   |                 7.8 |          9.3 |            1.2 |
| nan              |             34.3 |            42.1 |        7.2 |                 6.4 |          8.8 |            1.3 |

**Predicted cure (avg p_cure) — population mean 85.35%**
| marital_status   |     n |   pred_cure_pct |   gap_pp | verdict   |
|------------------|-------|-----------------|----------|-----------|
| common_law       | 10125 |           84.94 |    -0.42 | ok        |
| divorced         |  4960 |           85.31 |    -0.04 | ok        |
| married          | 26025 |           85.44 |     0.09 | ok        |
| separated        |  7657 |           85.22 |    -0.14 | ok        |
| single           | 22197 |           85.54 |     0.18 | ok        |
| undisclosed      |  3621 |           85.32 |    -0.03 | ok        |
| widowed          |  2412 |           84.57 |    -0.79 | ok        |
| nan              |  6680 |           85.52 |     0.17 | ok        |

**vulnerability_signal rate — population 16.67%**
| marital_status   |     n |   vuln_pct |   gap_pp | verdict   |
|------------------|-------|------------|----------|-----------|
| common_law       | 10125 |      14.36 |    -2.31 | ok        |
| divorced         |  4960 |      15.3  |    -1.36 | ok        |
| married          | 26025 |      14.95 |    -1.72 | ok        |
| separated        |  7657 |      32.43 |    15.76 | FLAG      |
| single           | 22197 |      14.84 |    -1.83 | ok        |
| undisclosed      |  3621 |      15.41 |    -1.26 | ok        |
| widowed          |  2412 |      17.41 |     0.75 | ok        |
| nan              |  6680 |      16.29 |    -0.38 | ok        |

_Verdict for marital_status: all groups within the 5pp band on predicted cure._

## citizenship_status

**Action distribution (% within group)**
| citizenship_status   |   call_best_time |   digital_nudge |   escalate |   hardship_referral |   no_contact |   payment_plan |
|----------------------|------------------|-----------------|------------|---------------------|--------------|----------------|
| citizen              |             34.5 |            41.7 |        7.1 |                 6.8 |          8.7 |            1.2 |
| permanent_resident   |             34.7 |            41.1 |        6.9 |                 7.2 |          8.9 |            1.2 |
| study_permit         |             34.6 |            41.2 |        7.2 |                 6.7 |          9.3 |            1   |
| work_permit          |             34.1 |            42   |        7   |                 7.1 |          8.6 |            1.2 |
| nan                  |             33.5 |            43.1 |        5.7 |                 8   |          7.6 |            2.1 |

**Predicted cure (avg p_cure) — population mean 85.35%**
| citizenship_status   |     n |   pred_cure_pct |   gap_pp | verdict   |
|----------------------|-------|-----------------|----------|-----------|
| citizen              | 64434 |           85.43 |     0.07 | ok        |
| permanent_resident   | 12145 |           85.06 |    -0.3  | ok        |
| study_permit         |  2614 |           84.89 |    -0.46 | ok        |
| work_permit          |  3612 |           85.34 |    -0.01 | ok        |
| nan                  |   872 |           85.5  |     0.15 | ok        |

**vulnerability_signal rate — population 16.67%**
| citizenship_status   |     n |   vuln_pct |   gap_pp | verdict   |
|----------------------|-------|------------|----------|-----------|
| citizen              | 64434 |      16.76 |     0.09 | ok        |
| permanent_resident   | 12145 |      16.43 |    -0.23 | ok        |
| study_permit         |  2614 |      16.14 |    -0.52 | ok        |
| work_permit          |  3612 |      16.31 |    -0.36 | ok        |
| nan                  |   872 |      16.06 |    -0.61 | ok        |

_Verdict for citizenship_status: all groups within the 5pp band on predicted cure._

## age_band

**Action distribution (% within group)**
| age_band   |   call_best_time |   digital_nudge |   escalate |   hardship_referral |   no_contact |   payment_plan |
|------------|------------------|-----------------|------------|---------------------|--------------|----------------|
| 18-24      |             34.2 |            41.8 |        6.8 |                 7   |          8.8 |            1.4 |
| 25-34      |             34.8 |            41.6 |        7   |                 6.8 |          8.6 |            1.2 |
| 35-44      |             34.1 |            41.8 |        7.3 |                 6.9 |          8.7 |            1.2 |
| 45-54      |             34.5 |            41.3 |        7.3 |                 7   |          8.8 |            1.1 |
| 55-64      |             35.4 |            40.9 |        6.9 |                 6.7 |          9   |            1   |
| 65+        |             34.6 |            42   |        6.7 |                 7   |          8.7 |            1   |
| nan        |             33.4 |            41.9 |        7.5 |                 6.3 |          9.9 |            1   |

**Predicted cure (avg p_cure) — population mean 85.35%**
| age_band   |     n |   pred_cure_pct |   gap_pp | verdict   |
|------------|-------|-----------------|----------|-----------|
| 18-24      | 16047 |           85.2  |    -0.15 | ok        |
| 25-34      | 22147 |           85.49 |     0.14 | ok        |
| 35-44      | 19737 |           85.38 |     0.03 | ok        |
| 45-54      | 15402 |           85.19 |    -0.17 | ok        |
| 55-64      |  6070 |           85.45 |     0.09 | ok        |
| 65+        |  3861 |           85.48 |     0.13 | ok        |
| nan        |   413 |           85.92 |     0.56 | ok        |

**vulnerability_signal rate — population 16.67%**
| age_band   |     n |   vuln_pct |   gap_pp | verdict   |
|------------|-------|------------|----------|-----------|
| 18-24      | 16047 |      16.31 |    -0.35 | ok        |
| 25-34      | 22147 |      16.5  |    -0.16 | ok        |
| 35-44      | 19737 |      16.65 |    -0.02 | ok        |
| 45-54      | 15402 |      16.64 |    -0.03 | ok        |
| 55-64      |  6070 |      15.82 |    -0.85 | ok        |
| 65+        |  3861 |      20.59 |     3.92 | ok        |
| nan        |   413 |      16.71 |     0.04 | ok        |

_Verdict for age_band: all groups within the 5pp band on predicted cure._

## newcomer_program_flag

**Action distribution (% within group)**
| newcomer_program_flag   |   call_best_time |   digital_nudge |   escalate |   hardship_referral |   no_contact |   payment_plan |
|-------------------------|------------------|-----------------|------------|---------------------|--------------|----------------|
| False                   |             34.5 |            41.6 |        7.1 |                 6.9 |          8.7 |            1.2 |
| True                    |             34.2 |            41.6 |        6.8 |                 7   |          9.2 |            1.3 |

**Predicted cure (avg p_cure) — population mean 85.35%**
| newcomer_program_flag   |     n |   pred_cure_pct |   gap_pp | verdict   |
|-------------------------|-------|-----------------|----------|-----------|
| False                   | 75986 |           85.42 |     0.07 | ok        |
| True                    |  7691 |           84.69 |    -0.67 | ok        |

**vulnerability_signal rate — population 16.67%**
| newcomer_program_flag   |     n |   vuln_pct |   gap_pp | verdict   |
|-------------------------|-------|------------|----------|-----------|
| False                   | 75986 |      16.72 |     0.06 | ok        |
| True                    |  7691 |      16.1  |    -0.57 | ok        |

_Verdict for newcomer_program_flag: all groups within the 5pp band on predicted cure._

## Overall

All groups across 5 protected attributes are within the 5pp fairness band on predicted cure.