# Text feature evaluation (5-fold cross-validation on public_500 labels)

TF-IDF (word 1-2 grams + char 3-5 grams) + logistic regression (class_weight='balanced').
ptp_intent_strength: Ridge regressor; metric is MAE.

## Notes (500 labels)

| field               |   n | overall        | per-class F1                                                                                                                                                 |
|---------------------|-----|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| hardship            | 500 | macro F1 0.98  | clear:0.953, none:0.986, possible:1.0                                                                                                                        |
| delay_reason        | 500 | macro F1 0.852 | dispute:0.667, forgot:1.0, other:0.853, reduced_income:0.788, unknown:0.954                                                                                  |
| ptp_mentioned       | 500 | macro F1 0.963 | false:0.969, true:0.957                                                                                                                                      |
| sentiment           | 500 | macro F1 0.558 | cooperative:0.693, distressed:0.579, frustrated:0.162, hostile:0.833, neutral:0.521                                                                          |
| vulnerability       | 500 | macro F1 0.886 | false:0.973, true:0.8                                                                                                                                        |
| next_step           | 500 | macro F1 0.931 | call_back:0.976, dispute_investigation:0.833, escalate_supervisor:0.906, hardship_plan_review:0.947, none:0.931, send_payment_link:0.979, stop_contact:0.941 |
| ptp_intent_strength | 207 | MAE 0.083      |                                                                                                                                                              |

## Transcripts (500 labels)

| field               |   n | overall        | per-class F1                                                                                                                                   |
|---------------------|-----|----------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| hardship            | 500 | macro F1 0.972 | clear:0.991, none:0.986, possible:0.938                                                                                                        |
| delay_reason        | 500 | macro F1 0.84  | dispute:0.952, forgot:0.927, other:0.723, reduced_income:0.79, unknown:0.808                                                                   |
| ptp_mentioned       | 500 | macro F1 0.903 | false:0.862, true:0.944                                                                                                                        |
| sentiment           | 500 | macro F1 0.517 | cooperative:0.49, distressed:0.536, frustrated:0.362, hostile:0.933, neutral:0.264                                                             |
| vulnerability       | 500 | macro F1 0.848 | false:0.942, true:0.754                                                                                                                        |
| next_step           | 500 | macro F1 0.84  | call_back:0.72, dispute_investigation:0.892, escalate_supervisor:0.955, hardship_plan_review:0.89, send_payment_link:0.918, stop_contact:0.667 |
| ptp_intent_strength | 373 | MAE 0.095      |                                                                                                                                                |

## Caveats
- Vulnerability positives: 55 (notes) / 82 (transcripts). F1 is low-variance; treat as a tip, not a verdict. The feature store exposes `vulnerability_signal = structured_vulnerability_flag OR (classifier_true AND confidence > 0.8)`.
- Delay reason collapsed to top-5 + 'other' to keep per-class support >=20.
- next_step is a diagnostic only (never a model input); feeds a later policy-vs-agent-step governance check.
- Rules (regex): dispute_mention, legal_threat_by_agent. Not scored here.