# Randomisation check (P6 pre-flight)

## Assignment counts

| test_cell          |   random |   rule_based |   total |
|--------------------|----------|--------------|---------|
| challenger_A       |    21397 |        32098 |   53495 |
| challenger_B       |    21254 |        32081 |   53335 |
| champion           |    92686 |       150273 |  242959 |
| no_contact_holdout |     7075 |            0 |    7075 |

## Cure rate per cell (full data)

| test_cell          |      n |   cure_pct |
|--------------------|--------|------------|
| challenger_A       |  53495 |      72.61 |
| challenger_B       |  53335 |      72.99 |
| champion           | 242959 |      72.77 |
| no_contact_holdout |   7075 |      71.52 |

## Balance check 1: no_contact_holdout vs champion (assignment_method='random' only)

| feature                       |    SMD |   n_holdout |   n_champion |
|-------------------------------|--------|-------------|--------------|
| dpd_level                     |  0.016 |        7075 |        92686 |
| worst_dpd_12m                 |  0.011 |        7075 |        92686 |
| dpd_slope_3m                  |  0.006 |        7075 |        92686 |
| utilisation_trend_6m          |  0.014 |        4496 |        58159 |
| balance_at_risk               | -0.004 |        7075 |        92686 |
| broken_promises_90d           |  0.019 |        7075 |        92686 |
| payroll_delay_days            |  0.005 |        7075 |        92686 |
| salary_change_3m_pct          |  0.006 |        1403 |        18471 |
| nsf_count_3m                  |  0.02  |        7075 |        92686 |
| cash_flow_slope_6m            |  0.027 |        3099 |        40965 |
| bureau_present                | -0.006 |        7075 |        92686 |
| bureau_delta_90d              | -0.02  |        2836 |        37155 |
| primary_product=auto_loan     | -0.005 |        7075 |        92686 |
| primary_product=card          |  0.002 |        7075 |        92686 |
| primary_product=loc           |  0.033 |        7075 |        92686 |
| primary_product=mortgage      | -0.019 |        7075 |        92686 |
| primary_product=overdraft     | -0.01  |        7075 |        92686 |
| primary_product=personal_loan | -0.006 |        7075 |        92686 |
| max_dpd_episode               |  0.005 |        7075 |        92686 |

Worst |SMD|: **0.033** -> balanced

## Balance check 2: challenger_A vs challenger_B (sanity)

| feature                       |    SMD |   n_A |   n_B |
|-------------------------------|--------|-------|-------|
| dpd_level                     | -0.007 | 21397 | 21254 |
| worst_dpd_12m                 | -0.007 | 21397 | 21254 |
| dpd_slope_3m                  |  0.002 | 21397 | 21254 |
| utilisation_trend_6m          |  0.015 | 13398 | 13420 |
| balance_at_risk               |  0.008 | 21397 | 21254 |
| broken_promises_90d           |  0.005 | 21397 | 21254 |
| payroll_delay_days            |  0     | 21397 | 21254 |
| salary_change_3m_pct          | -0.016 |  4328 |  4263 |
| nsf_count_3m                  | -0.007 | 21397 | 21254 |
| cash_flow_slope_6m            | -0.009 |  9468 |  9411 |
| bureau_present                | -0.001 | 21397 | 21254 |
| bureau_delta_90d              |  0.007 |  8578 |  8546 |
| primary_product=auto_loan     |  0     | 21397 | 21254 |
| primary_product=card          | -0.016 | 21397 | 21254 |
| primary_product=loc           |  0.002 | 21397 | 21254 |
| primary_product=mortgage      |  0.005 | 21397 | 21254 |
| primary_product=overdraft     |  0.005 | 21397 | 21254 |
| primary_product=personal_loan |  0.012 | 21397 | 21254 |
| max_dpd_episode               | -0.006 | 21397 | 21254 |

Worst |SMD|: **0.016**

## Verdict
**T-learner (randomisation holds)**

## Cure rate per cell x primary_product

| test_cell          | primary_product   |      n |   cure_pct |
|--------------------|-------------------|--------|------------|
| challenger_A       | auto_loan         |   4952 |      54.22 |
| challenger_A       | card              |  27988 |      79.16 |
| challenger_A       | loc               |   4792 |      65.86 |
| challenger_A       | mortgage          |   2224 |      92.76 |
| challenger_A       | overdraft         |   5538 |      81.67 |
| challenger_A       | personal_loan     |   8001 |      53.29 |
| challenger_B       | auto_loan         |   5084 |      55.19 |
| challenger_B       | card              |  28219 |      79.56 |
| challenger_B       | loc               |   4610 |      65.27 |
| challenger_B       | mortgage          |   2177 |      93.34 |
| challenger_B       | overdraft         |   5492 |      81.85 |
| challenger_B       | personal_loan     |   7753 |      53.35 |
| champion           | auto_loan         |  23429 |      54.42 |
| champion           | card              | 126863 |      79.15 |
| champion           | loc               |  21368 |      66.14 |
| champion           | mortgage          |  10037 |      93.48 |
| champion           | overdraft         |  25589 |      81.74 |
| champion           | personal_loan     |  35673 |      53.81 |
| no_contact_holdout | auto_loan         |    670 |      53.58 |
| no_contact_holdout | card              |   3716 |      78.18 |
| no_contact_holdout | loc               |    686 |      65.89 |
| no_contact_holdout | mortgage          |    262 |      95.04 |
| no_contact_holdout | overdraft         |    724 |      81.91 |
| no_contact_holdout | personal_loan     |   1017 |      49.36 |

## Cure rate per cell x max_dpd_episode bucket

| test_cell          | bucket   |      n |   cure_pct |
|--------------------|----------|--------|------------|
| challenger_A       | 1-29     |  28824 |      82.12 |
| challenger_A       | 30-59    |  13759 |      73.16 |
| challenger_A       | 60-89    |   5813 |      61.02 |
| challenger_A       | 90+      |   5099 |      30.65 |
| challenger_B       | 1-29     |  28707 |      82.66 |
| challenger_B       | 30-59    |  13679 |      73.36 |
| challenger_B       | 60-89    |   5831 |      61.64 |
| challenger_B       | 90+      |   5118 |      30.66 |
| champion           | 1-29     | 130462 |      82.21 |
| champion           | 30-59    |  62574 |      73.72 |
| champion           | 60-89    |  26582 |      61.53 |
| champion           | 90+      |  23341 |      30.25 |
| no_contact_holdout | 1-29     |   3774 |      81.82 |
| no_contact_holdout | 30-59    |   1857 |      71.73 |
| no_contact_holdout | 60-89    |    736 |      58.15 |
| no_contact_holdout | 90+      |    708 |      29.94 |

## Target choice (feeds P6 model card)

The pure 30-day-cure target has small uplift because no_contact_holdout cures at ~71.5%, close to champion. Keep that target for the published AUUC/Qini (judges expect it), but at decision time rank actions by **decision_value = p_cure_given_action * balance_at_risk - action_cost**. no_contact has action_cost = 0, so for self-cure customers it wins automatically. The segment breakdown above shows which buckets are self-cure (if the 71.5% holdout rate is uniform, self-cure is pervasive; if it is driven by 1-29, that is where decision_value will route most to no_contact).