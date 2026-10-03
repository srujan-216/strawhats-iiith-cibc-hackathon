# Layer 2 changelog

## 2026-10-03: configurable reasoning effort; A/B/C comparison attempted (INVALID, needs rerun)

**Changed**
- `llm.providers[*].reasoning_effort` in `config.yaml`: a level for every call, or a map per purpose
  (`plan`, `sql_fix`, `answer`, `answer_docs`, `default`). Sent as `reasoning_effort` only to providers that set it.
  The cache key includes each provider's model and effort, so changing either never reuses an old answer. Test added.
- `evaluate.py` rewritten for the real dev gold format: "Refuse..." answers are refusals; table answers are checked
  value by value within each question's tolerance; text answers are counted as "review". Tests added.
- `benchmark.py` writes `<out>.timing.csv` (seconds per question); `python -m src.layer2.compare` runs configs
  A (3.8-flash, default thinking), B (3.8-flash, plan/sql_fix medium, answer low) and C (3.5-flash with B's settings).

**Result: the comparison could not be done.** All three runs hit free-tier limits after 2 to 5 LLM calls, so
18 of 21 dev questions came back "all LLM providers unavailable" in every config. The accuracy (1 of 14) and
median time (0 s) in that run say nothing about the configs. Those result files were deleted.
- Gemini returned 429 "exceeded your current quota" (and 503 "high demand") during the runs; a single call
  succeeds when tried alone afterwards.
- Groq `openai/gpt-oss-120b`: the free tier allows about 8,000 tokens per minute, and our plan prompt alone is
  about 17,600 characters (roughly 4,500 tokens), so Groq can serve about one plan call a minute.
- `local` (localhost:8000) is not running, so it fails instantly.
- When every provider is cooling down, the gateway fails the question immediately instead of waiting.

**Before rerunning (proposed, not done)**
1. Gateway: when all providers are on cool-down, wait for the earliest one (up to ~70 s) instead of failing.
2. Cut the plan prompt (fewer tables and columns) so Groq can act as a real fallback.
3. Find Gemini's actual free-tier limits for each model (requests per day and tokens per minute) in AI Studio.
   If the daily limit is low, run A, B and C on a 6-question subset first.
