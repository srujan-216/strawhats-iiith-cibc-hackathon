# Collections 360

Unify fragmented bank collections data into a trusted 360° record, ask it anything in plain English,
and recommend the next best action — with reasons.

## Team

Straw Hats:

- Kondameedi Srujan Raj
- D Varshith Reddy
- G Swachatha
- T Sreenidhi

## What this is

Collections data at Maple Bank lives in five source systems (CRM, cards, loans, deposits, bureau)
with no shared customer key, so agents spend their day stitching context together instead of
helping customers. We built four layers that solve this end to end: a Golden C360 record with
survivorship + lineage; a plain-English Q&A assistant that always shows the SQL or policy source;
a feature store with text classifiers; and an uplift-based Next Best Action model with a policy
gate and SHAP explanations surfaced to the agent on a Streamlit desk. Safety is designed in:
every answer is grounded (no silent guesses), every recommendation goes through a hard policy
gate (hardship never harsher; cease-contact blocks outbound; insolvency/deceased block all
contact), no protected attribute enters any feature or decision, and the human agent is the
decision-maker — the system recommends, logs its reasoning, and records the agent's accept /
edit / reject with a reason code.

## Architecture

![Architecture](docs/architecture.png)

The diagram above is page 1 of our Phase 1 submitted design, drawn in TikZ/LaTeX by hand (not
AI-generated). The full 6-page design is `docs/StrawHats_SystemDesign.pdf`.

## How to run

Prerequisites: Python 3.10+, Git, ~12 GB free disk for the unpacked dataset.

```bash
# 1. Dataset (~2.3 GB zip, ~10 GB unpacked)
pip install -U huggingface_hub
hf download nuxsh/maple-collections-hackathon maple_collections_release.zip \
   --repo-type dataset --local-dir maple_data
cd maple_data && unzip maple_collections_release.zip && cd ..

# 2. Python environment
python -m venv .venv
# Windows:  .venv\Scripts\activate         Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# 3. Free-tier LLM keys (both free; the gateway skips providers with no key)
# Create a .env file in the repo root:
#   GEMINI_API_KEY=...        # from https://aistudio.google.com
#   GROQ_API_KEY=...          # from https://console.groq.com

# 4. Build the warehouse end-to-end
python run.py all             # register -> silver -> match -> c360 -> dq-report
python run.py features        # 1 M customers × 23 features
python run.py text-features   # train classifiers on 500 labels; score 760 k notes + 25 k transcripts
python run.py train           # 6 LightGBM NBA classifiers
python run.py score           # score all open cases -> gold.nba_recommendations
python run.py fairness        # reports/fairness_report.md
python run.py bench --out submission/benchmark_answers.csv --fresh

# 5. Agent Desk
python run.py app             # http://localhost:8501
```

### All run.py commands

| Command | Writes | Why |
|---|---|---|
| `register` | `raw.*`, `main.*` | load all 31 source files, honour `schema/schema.json` types |
| `silver [--sample N] [--tables ...]` | `silver.*` + `silver.fix_log` | clean, dedupe, parse DOBs, pad CIFs, repair DFI-0812, log every rule |
| `match [--sample N]` | `silver.id_xref`, `silver.steward_queue` | CRM dedupe + deterministic bridges + Splink (rule fallback) |
| `c360` | `gold.c360_customer / account / case / field_trust / dq_results` | survivorship-merged golden record; Q1–Q7 quality checks |
| `dq-report` | `reports/data_quality_report.md` | one row per data issue + how handled |
| `all [--sample N]` | all of the above in order | one command, from raw files to DQ report |
| `features [--sample N]` | `gold.features_offline / features_online` | 23 features per golden_id; parity-tested |
| `text-features` | `gold.text_features_notes / transcripts`, `models/text/*.joblib` | TF-IDF + logistic regression on the 500 public labels |
| `feature-report` | `reports/feature_report.md` | coverage, correlations, pair prune |
| `randomisation-check` | `reports/randomisation_check.md` | SMD balance of `test_cell` and segment cure rates |
| `train` | `models/nba/*.joblib`, `reports/model_card.md` | T-learner (one LightGBM per action), uplift vs no-contact |
| `score` | `gold.nba_recommendations` | batch-score all open cases through the policy gate |
| `score-case <case_id>` | — | sub-second lookup used by the Agent Desk |
| `fairness` | `reports/fairness_report.md` + append to `model_card.md` | protected-attribute gaps; the only module that reads them |
| `ask "<question>"` | — | free-form Q&A with SQL or sources shown |
| `bench [--split dev] [--out ...] [--pace-seconds N]` | `submission/benchmark_answers*.csv` | run the system on the benchmark; never hand-edited |
| `eval --answers ...` | `reports/benchmark_dev_eval.md` | dev-split scoring (gold answers only read here) |
| `app` | — | Streamlit Agent Desk on port 8501 |

## Demo

Video link: *(added before 21:00 IST on 4 Oct 2026)*

5-minute arc: Layer 2 ask box (certified answer + a protected-attribute refusal), opening a
hardship case on the Agent Desk, reading the three SHAP reasons + policy gate's blocked actions,
agent accept / edit with a reason code, and the fairness + audit report.

## What changed from our Phase 1 design

Baseline: `docs/StrawHats_SystemDesign.pdf` (the design we submitted in Phase 1). The build
revised the following technical/architecture decisions; reasons are in the model card and reports:

- **Text features — trained classifier instead of LLM at inference.** TF-IDF (word + char n-grams)
  + logistic regression on the 500 public note labels and 500 transcript labels; macro F1 0.97 on
  hardship. Predictable cost and latency, offline/online parity, no provider dependency per text
  record. Full numbers in `reports/text_feature_eval.md`.
- **LLM gateway — free-provider failover with caching.** OpenAI-compatible gateway to Google
  Gemini and Groq, with model-level fallback, 503 retry, cool-down waits, and a SQLite response
  cache. No single-provider dependency; no paid APIs at runtime.
- **RAG retrieval — BM25 over policy documents.** Fast, model-free, and sufficient on this corpus.
- **Identity resolution — Splink scoped to CRM dedupe.** Cross-source linkage is deterministic via
  bridge tables (`account_monthly_snapshot`, `collections_cases.coll_customer_ref`, external →
  deposits → CIF) at 97–100% coverage on four of five sources; Splink runs within
  `silver.customers` to catch duplicates the CRM pointer and `national_id_hash` miss. Simpler and
  auditable.
- **Feature store — own lightweight offline + online store** (DuckDB-backed) sharing one SQL
  definition per feature with a 1,000-key parity test. No Feast setup overhead; no feature loss.
- **NBA target — train on cure, decide on expected value.** The LightGBM T-learners predict cure;
  the live decision ranks actions by `p_cure(a) × balance_at_risk − action_cost(a)` so
  `action_cost = 0` for `no_contact` wins automatically on self-cure customers (the data shows a
  71.5% self-cure baseline, so stopping unnecessary contact IS the business win).

## AI tools used

- **Runtime (in the deployed system):** Google Gemini (free tier) and Groq (free tier) through our
  OpenAI-compatible gateway. Models in use: `gemini-3.5-flash`, `openai/gpt-oss-20b` with
  model-level fallbacks. No paid LLM APIs are used at runtime.
- **Build-time (pair-programming during development):** Claude (Anthropic) via Claude Code and
  Claude chat. Every suggestion was reviewed, tested, and committed by the team.

## Repo layout

```
src/layer1/        golden C360 pipeline (register / silver / match / C360 / DQ report)
src/layer2/        plain-English Q&A with SQL guard, free-LLM gateway, BM25 docs retrieval
src/layer3/        feature store + text classifier
src/layer4/        NBA T-learner, policy gate, SHAP explanations
src/governance/    fairness report (only module allowed to read protected attributes)
src/common/        config loading, audit log, sampling helper
app/               Streamlit Agent Desk
contracts/         c360_customer.yaml (data contract based on DC-COLL-001)
reports/           DQ, match, model card, feature + text-feature evals, fairness, L2 changelog
tests/             90 tests covering guard, policy gate, parity, grounding, no-protected-features
submission/        benchmark_answers.csv — our benchmark output (generated; never hand-edited)
docs/              architecture.png, Phase 1 design PDF, data-quality notes, screenshots
models/            trained classifiers (splink, nba, text); small, no PII
run.py             one entry point for every pipeline stage
config.yaml        data_dir, DuckDB path, LLM providers, memory limits
```

## Reports

- `reports/data_quality_report.md` — one row per data issue (silver fix log + Q1-Q7 gold checks + match summary)
- `reports/match_report.md` — identity resolution: precision / recall vs CRM-known duplicates, coverage by source
- `reports/model_card.md` — NBA T-learner per-action metrics, uplift vs no-contact, honesty notes, fairness summary
- `reports/randomisation_check.md` — SMD balance for `test_cell`, segment cure rates (feeds target choice)
- `reports/feature_report.md` — coverage, correlation with cure proxy, pairwise correlation pruning
- `reports/text_feature_eval.md` — 5-fold CV macro F1 per field (notes + transcripts) with caveats
- `reports/fairness_report.md` — action distribution, predicted cure, vulnerability-signal rate per group (5 pp band)
- `reports/l2_changelog.md`, `reports/l2_effort_comparison.md` — Layer 2 config decisions
- `reports/profile.md`, `reports/silver_fix_log.md` — source profile and rule-level cleaning summary
