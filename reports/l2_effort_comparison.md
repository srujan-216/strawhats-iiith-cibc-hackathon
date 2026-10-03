# Reasoning-effort comparison on the dev benchmark (21 questions)

| config | model | effort | ok / scored | accuracy | refusal acc | refusal recall | total s | median s | provider mix | provider failures |
|---|---|---|---|---|---|---|---|---|---|---|
| **A** | gemini-3.8-flash | default thinking | 4 / 14 | 0.286 | 1.000 | 1.000 | 270 | 7.2 | gemini 2, groq 20 | 26 |
| **B** | gemini-3.8-flash | plan medium, sql_fix medium, answer low | 3 / 14 | 0.214 | 0.952 | 0.667 | 216 | 9.2 | groq 19 | 27 |
| **C** | gemini-3.5-flash | plan medium, sql_fix medium, answer low | 4 / 14 | 0.286 | 1.000 | 1.000 | 216 | 10.6 | gemini 13, gemini(cached) 1, groq 16 | **14** |

(7 of 21 questions are text/document answers that the evaluator cannot auto-score, so the denominator is 14 table/refusal questions.)

## Recommendation: C (`gemini-3.5-flash`, plan medium / answer low)

- **Accuracy:** tied with A (4/14, 28.6 %), one ahead of B.
- **Refusals:** perfect, same as A; B missed one refusal (BQ-018 timed out) and only recalled 2 of 3 refusals.
- **Speed:** 216 s total vs 270 s for A; comparable to B. Median per question 10.6 s vs 7.2 s for A — slower per call but fewer retries so faster overall.
- **Provider mix:** C used Gemini 13 of 30 calls, A used it only 2. A was effectively running on Groq alone because `gemini-3.8-flash` kept returning 503 "high demand"; B had the same problem (0 Gemini calls at all).
- **Provider failures:** 14, roughly half of A (26) and B (27).

C gets us both the accuracy of A and real Gemini availability, at B's lower latency. `gemini-3.5-flash` is the older but more stable free-tier model.

The overall 28.6 % accuracy is poor regardless of config — S2 baseline work (prompt rewrites, metric routing, SQL-fix loop) is where that moves. This test is only about the LLM-tuning knobs.

Caveats:
- Only 14 auto-scored questions; small sample. The ranking (C ≥ A > B) is directional, not statistical.
- All three runs started from an empty cache; a cache hit from an earlier run was treated as C using Gemini.
- Gemini free-tier limits are not published in a header, so cool-down waits are our best guess. If Gemini daily quota resets fire during a benchmark, numbers can shift.
