# Feature report (1,001,069 customers)

Target used here is a proxy: `cured` = any of the customer's collections cases cured. Layer 4 (P6) replaces this with a point-in-time target per decision_date (cured within 30 days). Correlations are a quick sanity check, not a model selection.

## Coverage and correlation with cured proxy (sorted by |corr|)

| feature                        |   coverage_pct |   corr_cured |
|--------------------------------|----------------|--------------|
| worst_dpd_12m                  |          100   |        0.174 |
| txt_ptp_mentioned              |          100   |        0.133 |
| txt_delay_reason               |          100   |        0.126 |
| txt_sentiment                  |          100   |        0.122 |
| bureau_present                 |          100   |       -0.078 |
| txt_hardship_signal            |          100   |        0.072 |
| broken_promises_90d            |          100   |        0.066 |
| dpd_level                      |          100   |        0.06  |
| contacts_last_7d               |          100   |        0.054 |
| bureau_delta_90d               |           46.4 |       -0.043 |
| nsf_count_3m                   |          100   |        0.034 |
| best_time_band_hour            |            1.3 |        0.031 |
| txt_dispute_mention            |          100   |        0.028 |
| balance_at_risk                |          100   |        0.022 |
| vulnerability_signal           |          100   |        0.018 |
| txt_ptp_intent_strength        |            5.6 |       -0.015 |
| dpd_slope_3m                   |          100   |        0.013 |
| promise_due_vs_payday_gap_days |            1.6 |       -0.009 |
| payroll_delay_days             |          100   |        0.006 |
| utilisation_trend_6m           |           48.8 |        0.005 |
| answer_rate_30d                |            4.9 |       -0.004 |
| salary_change_3m_pct           |           23.5 |       -0.003 |
| cash_flow_slope_6m             |           51.3 |        0.001 |

## Pairwise correlation prune (|r| > 0.9)

(no numeric pair above threshold - no pruning needed)

## Kept list (23 of 23 features)

dpd_level, worst_dpd_12m, dpd_slope_3m, utilisation_trend_6m, balance_at_risk, broken_promises_90d, promise_due_vs_payday_gap_days, payroll_delay_days, salary_change_3m_pct, nsf_count_3m, cash_flow_slope_6m, bureau_present, bureau_delta_90d, contacts_last_7d, answer_rate_30d, best_time_band_hour, txt_hardship_signal, txt_delay_reason, txt_ptp_mentioned, txt_ptp_intent_strength, txt_sentiment, vulnerability_signal, txt_dispute_mention

## Dropped
(none - all features kept)

## Notes
- IV / PSI left to a point-in-time build with a real target; the proxy here is biased by the order of case opens.
- bureau_delta_90d coverage ~48% is by design (CLAUDE §bureau coverage); the companion `bureau_present` flag lets the model treat missingness explicitly.
- Protected or proxy columns (gender, age, FSA income, majority_language, cpp_oas, ccb) do NOT appear here; src/governance/fairness.py is the only module allowed to read them.