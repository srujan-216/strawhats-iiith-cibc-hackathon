# CLAUDE.md — Straw Hats: Collections 360 (CIBC Collections Hackathon, build phase)

You are working in our team repo. Read this file fully before every task. It is the source of truth
for goals, rules and conventions. If a request conflicts with a rule here, stop and say so.

## 1. Goal and deadline

Build a working version of our design: **all four layers working end to end, with Next Best Action (NBA)
built in depth**, on the real Maple Bank dataset.

- Hard deadline: **4 Oct 2026, 21:00 IST**. Commits after that are not counted.
- Extra benchmark questions are released at **19:00 IST on 4 Oct**. The system must answer them as it
  is, with one command. Answers must never be edited by hand.
- Judges also ask unseen questions live, so Layer 2 must generalise, not memorise the benchmark.

Judging: technical quality and working demo 30% (benchmark score counts here), business understanding 20%,
presentation 20%, innovation 15%, team work 15% (commit history).

Two people build. Ownership follows the hardware:
| Person | Machine | Owns |
|---|---|---|
| Srujan | laptop (CPU) | Layer 1 (cleaning, identity resolution, C360, DQ report, contract), Layer 2 (Q&A, benchmark), Agent Desk app, README |
| Varshith | GPU workstation | Layer 3 (features, text/voice features), Layer 4 (NBA model, policy gate, explanations), all heavy/full-data runs, governance reports |

Anything slow (full-data runs, LLM labelling, embeddings, Whisper, model training, full Splink run)
runs on Varshith's GPU machine. Srujan develops on `--sample` and hands full runs over.

## 2. Data facts (verify against `maple_collections_release/README.md` and `DATA_DICTIONARY.xlsx`)

- One fictional bank, 1,000,000 customers (1,020,000 CRM records: duplicates exist), Oct 2016 to Sep 2026.
  **Snapshot / "today" = 2026-09-28** unless a question gives `as_of_date`.
- 31 tables: CSV (small/core), Parquet by year (history: ~20M loan instalments, ~10M transactions,
  ~8M card statements, account_monthly_snapshot, bureau_history, salary_credit_history), JSON transcripts
  (25,000), policy documents, optional WAV (2,000).
- **Five source systems, each with its own customer key** (cards, loans, deposits, CRM, collections).
  Matching them into one `golden_id` with a confidence is a core deliverable.
- Data quality issues are deliberate: duplicates, missing values, NA codes, mixed date formats,
  leading-zero IDs, mismatched IDs, schema drift (e.g. `channel` vs `channel_v2`).
- `labels/` holds dev gold answers, the answers template and **500 public labels each for notes and
  transcripts** (use these to measure LLM feature accuracy).
- Example data contract **DC-COLL-001** is in `files/docs/data_contracts/` — base our contract on it.
- Use **DuckDB or Polars** for large tables. Never load the big Parquet tables fully into pandas.

### Protected attributes — never in any decision, feature, model, rule or Q&A answer
gender, marital status, citizenship, household size/dependants, newcomer, accessibility, vulnerability
type, accent (and voice biometrics such as pitch). Also exclude proxies we committed to: `age`, `age_band`,
`cpp_oas_deposit_flag`, `ccb_deposit_flag`, FSA / postal-area income fields, `majority_language`.
They may only be read inside `src/governance/fairness.py` to measure outcome gaps between groups.

## 3. Architecture (keep these module boundaries)

```
sources -> L1 raw -> silver -> identity resolution -> golden C360 (DuckDB tables + contract)
        -> L2 Q&A (read-only)            -> Agent Desk (Streamlit)
        -> L3 feature store -> L4 NBA model -> policy gate -> explanation -> Agent Desk -> human decision
governance across all: role-based views, audit log, monitoring, fairness, human review points H1-H5
```

| Layer | Path | Key tools |
|---|---|---|
| 1 Data Product Factory | `src/layer1/` | DuckDB, Polars, Splink (probabilistic matching), Pandera or plain SQL checks |
| 2 Insight and NLP | `src/layer2/` (exists) | sqlglot guard, free-LLM gateway `src/layer2/llm.py`, BM25 (+ embeddings if time) |
| 3 Feature Store | `src/layer3/` | feature definitions in code, offline Parquet + online DuckDB table (Feast only if it installs quickly) |
| 4 Models and Decisioning | `src/layer4/` | LightGBM T-learner uplift, SHAP, rule-based policy gate, template explanations |
| Agent Desk | `app/` | Streamlit |
| Governance | `src/governance/` | roles, audit, override log, fairness report |

All LLM calls go through `src/layer2/llm.py` (the model gateway). Do not call model APIs anywhere else.

**Free LLMs only. No paid APIs, ever.** The gateway speaks the OpenAI-compatible protocol to:
`local` (vLLM or Ollama serving Qwen2.5 on Varshith's GPU, unlimited), `gemini` (Google AI Studio free
tier) and `groq` (Groq free tier). Routes in `config.yaml` pick the order per task: `default` for Q&A,
`bulk` (local GPU only) for labelling thousands of notes. Free tiers have per-minute and per-day limits,
so: never loop LLM calls without the gateway's cache, never send bulk jobs to Gemini/Groq, and keep
prompts small (only the relevant tables/columns). Do not add the `anthropic` or `openai` paid SDKs.

## 4. Non-negotiable rules

1. **AI is read-only.** Layer 2 and the Agent Desk open DuckDB with `read_only=True`. Generated SQL passes
   `src/layer2/guard.py` (one SELECT, allowlisted tables, no DDL/DML, no file functions, no protected
   columns, row limit, timeout). Do not weaken the guard; extend `tests/test_guard.py` when you touch it.
2. **No leakage of gold data.** Runtime code must never read `labels/`, the `hidden` schema, or the
   benchmark columns `should_refuse`, `refusal_reason`, `metric_id`, `expected_tables`, `grading_rubric`,
   `tolerance`. Only `src/layer2/evaluate.py` may read gold answers, for scoring dev.
3. **Never hand-edit benchmark answers.** The CSV comes only from `python run.py bench`.
4. **Every recommendation shown to an agent has a plain-English reason** (top reasons + evidence).
5. **A human reviews anything that affects a customer.** The system recommends; the agent accepts, edits
   or rejects with a reason code; hardship/vulnerable/escalated cases go to a supervisor queue.
6. **Hardship flags protect, never penalise.** A hardship flag routes to supportive actions and a
   certified agent; it must never increase contact pressure.
7. **Never modify or delete source files.** Raw data is immutable; every cleaning change is logged with
   rule name and row count (feeds the data quality report). No silent `dropna()` or silent dedupe.
8. **Outcome columns are labels, never features:** `cure_flag`, `days_to_cure`, `outcome`,
   `dpd_at_day_*`, `overdue_at_day_*`, `roll_forward_count`, `nba_accepted_flag`, `human_override_flag`,
   and anything dated after the decision timestamp.
9. Never commit data, the DuckDB file, API keys or `.env`. No paid LLM APIs.

## 5. Design decisions to implement (from our submitted design)

- **Identity resolution:** match source keys, not rows. (1) collapse CRM duplicates
  (`duplicate_of_crm_id`, `national_id_hash`); (2) deterministic links via tables that carry account ID +
  `crm_customer_id` (account_monthly_snapshot, salary_credit_history, contact_history, promises_to_pay,
  agent_notes); (3) Splink on name (+ nicknames / `preferred_name`), DOB (incl. day/month swap), phone
  (last 10 digits), postal code / FSA, email; thresholds: >= 0.95 auto-merge, 0.70–0.95 steward queue,
  < 0.70 separate; (4) report precision/recall of Splink using deterministic links as known truth.
- **Survivorship:** consent = most restrictive; hardship/vulnerability/insolvency/deceased/cease-contact
  = true if any source true; contact details = most recently verified; balances/DPD = system of record.
- **Outputs:** `id_xref`, `c360_customer`, `c360_account`, `c360_case`, each field with lineage
  (source, refreshed_at, dq_status).
- **Layer 2:** certified metrics from `metric_definitions` first; NL-to-SQL otherwise; text questions via
  notes/transcripts SQL retrieval or policy-doc RAG (current versions only); grounding check; refusals with
  a reason.
- **Features (examples):** dpd level and 3-month slope, broken promises 90d, promise-due vs payday gap,
  payroll delay, salary change, NSF count, cash-flow trend, utilisation trend, bureau delta, answer rate,
  best time band, contacts in last 7 days; text: hardship signal, delay reason, promise intent, sentiment.
  Each feature has a catalog entry: name, entity, type, meaning, recipe, sources, refresh, owner, version,
  why we keep it, accuracy (LLM features).
- **Same values for training and live scoring:** one feature definition function used by both the
  offline point-in-time build and the online lookup; a parity test compares them.
- **NBA:** actions = no contact, SMS/email pay link, call in best time band, payment plan, hardship
  referral, escalate (recommend only). T-learner uplift on randomised `test_cell` history (check
  randomisation first; fall back to per-action propensity and say so). Choose max
  `(p_a - p_no_contact) * balance_at_risk - cost_a` under channel capacity.
- **Policy gate (always after the model):** insolvency/deceased → no contact; cease-contact/open dispute
  → no contact; representative → contact representative; consent, 7-day contact cap, permitted hours in
  customer time zone; hardship → supportive only + `hardship_programs` eligibility; vulnerable →
  certified agents.
- **Explanation:** SHAP top 3 → fixed plain-English templates + evidence (note id / policy section) +
  confidence + policy checks passed. The LLM does not write explanations.

## 6. Compute rules (two machines)

- **Every heavy job is resumable and cached**: process in batches, write each batch to
  `warehouse/cache/<job>/part-XXXX.parquet`, skip finished parts on restart, log progress to
  `logs/<job>.log`. Run long jobs with `nohup` or `tmux` so they survive disconnects.
- **GPU settings (Varshith):** local LLM via vLLM or Ollama (Qwen2.5-7B-Instruct; 14B if VRAM >= 24 GB),
  `sentence-transformers` with `device="cuda"`, `faster-whisper` with `device="cuda", compute_type="float16"`,
  LightGBM CPU is fine (GPU optional). Check `nvidia-smi` and VRAM before choosing model sizes.
- **Every model choice is a config value** in `config.yaml` (provider, model, device, batch size), so the
  same code runs on the laptop (free APIs / CPU) and the GPU machine (local).
- **Shared local LLM:** Varshith runs a vLLM OpenAI-compatible server (port 8000) and shares it with
  Srujan over Tailscale (free). Srujan sets the `local` provider's `base_url` to Varshith's Tailscale IP.
  When it is down, the gateway falls back to Gemini/Groq automatically.
- **Sharing results:** small outputs (reports, CSVs, YAML, model files < 50 MB) go in git. Large outputs
  (DuckDB, caches, embeddings) stay local; each machine can rebuild them with `run.py`. If Srujan needs
  Varshith's large outputs, export Parquet and share via drive, never git.
- Layer 3/4 must not wait for the C360: start from `main.*` / silver tables keyed by `crm_customer_id` and
  `case_id`, then switch the key to `golden_id` once `id_xref` exists (one join, behind a function).

## 7. How to work

- **Plan first.** For any task bigger than a small fix: read the relevant code and data, then write a
  short plan (files, steps, how you'll verify) and wait for approval.
- **Inspect before you assume.** Check real column names, types, null rates and sample values with DuckDB
  before writing transforms. When the dictionary and the data disagree, trust the data and note it in
  `docs/DATA_NOTES.md`.
- **Develop on a sample, finish on full data.** Every pipeline step accepts `--sample N` (customer-level
  sample, fixed seed 42) and must also run on the full dataset.
- **Verify with numbers.** After each step print row counts in/out, rows changed per rule, and timings.
  Add or update tests in `tests/` for logic (guard, survivorship, matching rules, feature parity, policy
  gate).
- **One command per stage**, added to `run.py`: `register`, `silver`, `match`, `c360`, `dq-report`,
  `features`, `train`, `score`, `bench`, `eval`, and `app` (Streamlit). `python run.py all` rebuilds
  everything from raw.
- **Commit small and often** with clear messages (`l1: add phone normaliser + tests`). Never rewrite
  shared history. Srujan works on `srujan/*` branches, Varshith on `varshith/*`; merge to `main` through
  short PRs at least every few hours so the other person always has a working `main`.
- **Keep the README current:** add to "What changed from our design" and "AI tools we used" whenever
  something changes. Be honest that Claude Code wrote code under team review.
- Prefer simple, explainable code a student can defend in a 5-minute demo. Flag anything too clever.
- Do not add heavy dependencies without asking. Pin versions in `requirements.txt`.
- If something is ambiguous, ask one sharp question and propose a default.

## 8. Deliverables (paths are fixed)

| Deliverable | Path | Owner |
|---|---|---|
| Code, one-command run | repo root, `run.py` | both |
| README (how to run, what changed, AI tools) | `README.md` | Srujan |
| Architecture diagram (final) | `docs/architecture.pdf` | Srujan |
| Data contract (YAML, based on DC-COLL-001) | `contracts/c360_customer.yaml` | Srujan |
| Data quality report (issue, records affected, handling) | `reports/data_quality_report.md` (generated) | Srujan |
| Benchmark answers | `submissions/benchmark_answers.csv` (generated) | Srujan |
| Feature report, model card, fairness and monitoring reports | `reports/` (generated) | Varshith |
| Demo video (≤5 min), deck (≤10 slides PDF) | outside repo | both |

Scope cuts agreed for a two-person team: our own feature store instead of Feast; steward queue as a
simple table view; voice features only if GPU time is free after text features; no embeddings for RAG
unless BM25 retrieval is clearly failing.
