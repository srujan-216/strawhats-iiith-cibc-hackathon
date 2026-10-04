# NBA model card

## Design
- **T-learner**: one LightGBM binary classifier per action (p_cure | action, features).
- **Target**: `collections_cases.cure_flag` (cured within the case).
- **Decision**: argmax over allowed actions of  `p_cure(a) * balance_at_risk - action_cost(a)`.
- **Policy gate** runs after the model and can block the top action; next allowed wins.
- **Features**: 24 (16 numeric + 8 text-derived). Protected / proxy attributes NOT in the input set.

## Actions and training counts

| action            |   training rows |   action_cost ($) |
|-------------------|-----------------|-------------------|
| no_contact        |            7075 |              0    |
| digital_nudge     |           73393 |              0.05 |
| call_best_time    |           41322 |              2.5  |
| payment_plan      |            6800 |              1    |
| hardship_referral |           17764 |              3    |
| escalate          |           28774 |             10    |

## Per-action classifier metrics (20% hold-out)

| action            |   n_test |   cured_rate |   AUC |   PR-AUC |   Brier | status   |
|-------------------|----------|--------------|-------|----------|---------|----------|
| no_contact        |     1415 |        0.715 | 0.933 |    0.978 |  0.0838 | ok       |
| digital_nudge     |    14679 |        0.823 | 0.971 |    0.994 |  0.0525 | ok       |
| call_best_time    |     8265 |        0.781 | 0.974 |    0.994 |  0.0477 | ok       |
| payment_plan      |     1360 |        0.161 | 0.974 |    0.946 |  0.0278 | ok       |
| hardship_referral |     3553 |        0.253 | 0.953 |    0.942 |  0.0409 | ok       |
| escalate          |     5755 |        0.33  | 0.981 |    0.981 |  0.019  | ok       |

## Predicted uplift vs no_contact baseline (eval on no_contact_holdout customers)

| action            |   mean uplift |   p10 uplift |   p90 uplift |
|-------------------|---------------|--------------|--------------|
| digital_nudge     |        0.1664 |      -0.0828 |       0.8803 |
| call_best_time    |        0.1891 |      -0.0228 |       0.8523 |
| payment_plan      |       -0.0128 |      -0.1313 |       0.0361 |
| hardship_referral |        0.0173 |      -0.0838 |       0.1028 |
| escalate          |        0.2357 |      -0.0098 |       0.8801 |

## Honesty notes
- `payment_plan`, `hardship_referral`, `escalate` are **observational** (not randomised). Their classifiers predict p_cure WHEN they were applied; the uplift column treats them as treatments but confounding is possible. For live decisions these actions are gated by the policy module anyway (hardship routes supportive, escalate is late-stage only), so uplift is a diagnostic, not the decision driver.
- The randomisation check (`reports/randomisation_check.md`) confirms the champion / no_contact_holdout contrast is clean (worst |SMD| = 0.033).
- Pure 30-day-cure uplift is small (no_contact baseline 71.5%); `decision_value` with `action_cost=0` for no_contact is why the system still saves money - it stops dialling customers who were going to self-cure.
- `action_cost` values are illustrative; a cost study should replace them before prod.

## Fairness

Report: `reports/fairness_report.md`. Measured on 5 protected attributes using the method in src/governance/fairness.py (5pp fairness band on predicted cure).
**All groups fall within the 5pp band on predicted cure.** No live recommendation is changed by fairness; the module is report-only (see CLAUDE.md §2).
