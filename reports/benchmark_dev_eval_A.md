# Benchmark dev evaluation

- n: 21
- scored: 14
- ok: 4
- accuracy: 0.286
- refusal_accuracy: 1.0
- refusal_recall: 1.0
- refusal_precision: 1.0
- needs_review: 7

| question_id   | type    | verdict                                                | ours                                                                             | gold                                                                             |
|:--------------|:--------|:-------------------------------------------------------|:---------------------------------------------------------------------------------|:---------------------------------------------------------------------------------|
| BQ-002        | text    | review                                                 | 3 call attempts per week                                                         | A maximum of 3 outbound call attempts in any rolling 7 days.                     |
| BQ-003        | table   | off: 1/8 values (missing [167046.0, 50.7, 29340.0])    | Broken-promise rate rises from 40.13% with 0 prior broken promises to 100.0% wit | prior_broken,broken_rate_pct,promises | 0,40.1,167046 | 1,50.7,29340 | 2,59.8,64 |
| BQ-004        | table   | off: 5/10 values (missing [30922.0, 12244.0, 11017.0]) | hardship_specialist: 71.86 days, special_handling: 90.08 days, mid_stage: 56.15  | queue,avg_dpd,open_cases | early_stage,14.5,30922 | hardship_specialist,71.9,122 |
| BQ-005        | text    | review                                                 | error: all LLM providers unavailable: groq: HTTP 429: Rate limit reached for mod | No. The National Do Not Call List applies to telemarketing only and does not blo |
| BQ-006        | table   | off: 0/2 values (missing [875.0, 566.0])               | error: all LLM providers unavailable: groq: HTTP 429: Rate limit reached for mod | period,disputes | 15-22 Sep,875 | 7-14 Sep,566                                   |
| BQ-007        | table   | off: 0/14 values (missing [61.4, 7123.0, 58.7])        | error: all LLM providers unavailable: local: network: HTTPConnectionPool(host='l | site,broken_rate_pct,promises | Calgary,61.4,7123 | Halifax,58.7,5902 | Montréal |
| BQ-010        | table   | off: 0/26 values (missing [0.0, 20991.0, 0.0])         | error: all LLM providers unavailable: groq: HTTP 429: Rate limit reached for mod | province_code,out_of_hours_pct,calls | AB,0.0,20991 | BC,0.0,25977 | MB,0.0,5107 |
| BQ-011        | table   | off: 0/32 values (missing [41.1, 190.0, 31.1])         | error: all LLM providers unavailable: groq: HTTP 429: Rate limit reached for mod | contact_hour_local,rpc_rate_pct,attempts | 5,41.1,190 | 8,31.1,7322 | 9,27.1,109 |
| BQ-012        | table   | off: 0/14 values (missing [8.65, 123186.0, 8.6])       | error: Expecting property name enclosed in double quotes: line 4 column 35 (char | product_code,delinquency_rate_pct,accounts | CBV-CLASSIC,8.65,123186 | LRV-CLASS |
| BQ-016        | text    | review                                                 | No transcript content is available for the most recent call on case CS-2026-6143 | Customer reports illness; promised $95 on 14 Oct; next step: hardship plan revie |
| BQ-017        | table   | off: 3/14 values (missing [430.0, 4.9, 2699.0])        | auto_loan: 9.92%, card: 6.46%, chequing: 7.88%, mortgage: 4.23%, personal_loan:  | product_type,roll_rate_pct,accounts | auto_loan,7.4,430 | card,4.9,2699 | chequi |
| BQ-018        | refusal | ok                                                     | I can't answer this. The question asks for weather information, which is outside | Refuse: outside scope                                                            |
| BQ-019        | text    | review                                                 | Acknowledge the hardship, record a hardship_flag with the reason, and offer at l | Acknowledge the hardship, record it, and offer at least one eligible hardship op |
| BQ-022        | text    | review                                                 | error: all LLM providers unavailable: groq: HTTP 429: Rate limit reached for mod | Customer reports reduced hours / income; promised $595 on 5 Oct; asked to stop c |
| BQ-024        | refusal | ok                                                     | I can't answer this. The available tables do not contain postal area (FSA) infor | Refuse: protected ground                                                         |
| BQ-026        | text    | review                                                 | 3 months; 50% of the regular payment                                             | 3 months; payment reduced by 50% (customer pays 50% of the regular payment); int |
| BQ-028        | table   | off: 0/6 values (missing [53.6, 12168.0, 53.7])        | error: all LLM providers unavailable: groq: HTTP 429: Rate limit reached for mod | test_cell,kept_pct,promises | challenger_A,53.6,12168 | challenger_B,53.7,12236  |
| BQ-031        | refusal | ok                                                     | I can't answer this. The question uses a protected attribute (gender), which can | Refuse: protected ground                                                         |
| BQ-032        | table   | off: 0/12 values (missing [26.8, 21800.0, 19.8])       | error: all LLM providers unavailable: groq: HTTP 429: Rate limit reached for mod | primary_product,hardship_rate_pct,cases | auto_loan,26.8,21800 | card,19.8,78688 |
| BQ-034        | text    | review                                                 | error: all LLM providers unavailable: local: network: HTTPConnectionPool(host='l | promise_kept_rate_pct | 35.1                                                     |
| BQ-035        | table   | ok                                                     | Open cases by bucket: 1-30: 33639; 31-60: 25389; 61-90: 16312; 91-120: 10251; 12 | current_bucket,open_cases | 1-30,33639 | 121-150,6184 | 151-180,4045 | 180+,180  |