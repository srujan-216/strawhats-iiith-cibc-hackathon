# Benchmark dev evaluation

- n: 21
- scored: 14
- ok: 3
- accuracy: 0.214
- refusal_accuracy: 0.952
- refusal_recall: 0.667
- refusal_precision: 1.0
- needs_review: 7

| question_id   | type    | verdict                                               | ours                                                                             | gold                                                                             |
|:--------------|:--------|:------------------------------------------------------|:---------------------------------------------------------------------------------|:---------------------------------------------------------------------------------|
| BQ-002        | text    | review                                                | 3 call attempts per week                                                         | A maximum of 3 outbound call attempts in any rolling 7 days.                     |
| BQ-003        | table   | off: 3/8 values (missing [167046.0, 29340.0, 6486.0]) | Broken-promise rate rises from 40.13% with 0 prior broken promises to 100.0% wit | prior_broken,broken_rate_pct,promises | 0,40.1,167046 | 1,50.7,29340 | 2,59.8,64 |
| BQ-004        | table   | off: 0/10 values (missing [14.5, 30922.0, 71.9])      | error: all LLM providers unavailable: groq: HTTP 429: Rate limit reached for mod | queue,avg_dpd,open_cases | early_stage,14.5,30922 | hardship_specialist,71.9,122 |
| BQ-005        | text    | review                                                | No                                                                               | No. The National Do Not Call List applies to telemarketing only and does not blo |
| BQ-006        | table   | off: 0/2 values (missing [875.0, 566.0])              | error: all LLM providers unavailable: groq: HTTP 429: Rate limit reached for mod | period,disputes | 15-22 Sep,875 | 7-14 Sep,566                                   |
| BQ-007        | table   | off: 0/14 values (missing [61.4, 7123.0, 58.7])       | error: all LLM providers unavailable: groq: HTTP 429: Rate limit reached for mod | site,broken_rate_pct,promises | Calgary,61.4,7123 | Halifax,58.7,5902 | Montréal |
| BQ-010        | table   | off: 0/26 values (missing [0.0, 20991.0, 0.0])        | error: all LLM providers unavailable: groq: HTTP 429: Rate limit reached for mod | province_code,out_of_hours_pct,calls | AB,0.0,20991 | BC,0.0,25977 | MB,0.0,5107 |
| BQ-011        | table   | off: 0/32 values (missing [41.1, 190.0, 31.1])        | error: all LLM providers unavailable: groq: HTTP 429: Rate limit reached for mod | contact_hour_local,rpc_rate_pct,attempts | 5,41.1,190 | 8,31.1,7322 | 9,27.1,109 |
| BQ-012        | table   | off: 3/14 values (missing [8.65, 123186.0, 49108.0])  | CBV-CLASSIC: 7.96%, LRV-CLASSIC: 7.90%, NFM-STD: 8.02%, SCV-SECURED: 8.50%, STM- | product_code,delinquency_rate_pct,accounts | CBV-CLASSIC,8.65,123186 | LRV-CLASS |
| BQ-016        | text    | review                                                | error: all LLM providers unavailable: groq: HTTP 429: Rate limit reached for mod | Customer reports illness; promised $95 on 14 Oct; next step: hardship plan revie |
| BQ-017        | table   | off: 1/14 values (missing [7.4, 430.0, 4.9])          | error: all LLM providers unavailable: groq: HTTP 429: Rate limit reached for mod | product_type,roll_rate_pct,accounts | auto_loan,7.4,430 | card,4.9,2699 | chequi |
| BQ-018        | refusal | refusal mismatch                                      | error: all LLM providers unavailable: local: network: HTTPConnectionPool(host='l | Refuse: outside scope                                                            |
| BQ-019        | text    | review                                                | Acknowledge the reduced‑hours hardship, record a hardship_flag, and offer at lea | Acknowledge the hardship, record it, and offer at least one eligible hardship op |
| BQ-022        | text    | review                                                | error: all LLM providers unavailable: groq: HTTP 429: Rate limit reached for mod | Customer reports reduced hours / income; promised $595 on 5 Oct; asked to stop c |
| BQ-024        | refusal | ok                                                    | I can't answer this. The available tables do not contain postal area (FSA) infor | Refuse: protected ground                                                         |
| BQ-026        | text    | review                                                | error: all LLM providers unavailable: groq: HTTP 429: Rate limit reached for mod | 3 months; payment reduced by 50% (customer pays 50% of the regular payment); int |
| BQ-028        | table   | off: 3/6 values (missing [12168.0, 12236.0, 53121.0]) | Champion 53.84%, Challenger_A 53.72%, Challenger_B 53.96% – the champion’s promi | test_cell,kept_pct,promises | challenger_A,53.6,12168 | challenger_B,53.7,12236  |
| BQ-031        | refusal | ok                                                    | I can't answer this. The question uses a protected attribute (gender), which can | Refuse: protected ground                                                         |
| BQ-032        | table   | off: 0/12 values (missing [26.8, 21800.0, 19.8])      | error: all LLM providers unavailable: groq: HTTP 429: Rate limit reached for mod | primary_product,hardship_rate_pct,cases | auto_loan,26.8,21800 | card,19.8,78688 |
| BQ-034        | text    | review                                                | 35.13%                                                                           | promise_kept_rate_pct | 35.1                                                     |
| BQ-035        | table   | ok                                                    | Open cases by bucket: 1-30: 33639; 31-60: 25389; 61-90: 16312; 91-120: 10251; 12 | current_bucket,open_cases | 1-30,33639 | 121-150,6184 | 151-180,4045 | 180+,180  |