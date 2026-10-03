# Straw Hats: Collections 360

CIBC Collections Hackathon, build phase. Unify Maple Bank's collections data into a golden
customer record (C360), answer plain-English questions with the SQL or source shown, and
recommend a Next Best Action with plain-English reasons and a human decision.

Team: Kondameedi Srujan Raj, D Varshith Reddy, G Swachatha, T Sreenidhi

## How to run

```bash
# 1. data (about 10 GB free disk)
pip install -U huggingface_hub
hf download nuxsh/maple-collections-hackathon --repo-type dataset --local-dir maple_data
cd maple_data && unzip maple_collections_release.zip && cd ..

# 2. environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# free LLM providers only (set the ones you have; missing keys are skipped)
export GEMINI_API_KEY=...             # Google AI Studio free tier
export GROQ_API_KEY=...               # Groq free tier
# local model on the team GPU: see docs/VARSHITH_HANDOUT.md (vLLM, OpenAI-compatible, port 8000)

# 3. pipeline
python run.py register                # load all sources into DuckDB (raw + typed)
python run.py profile                 # reports/profile.md
python run.py ask "What is the cure rate for card cases in the last 90 days?"
python run.py bench --split dev --out submissions/benchmark_answers_dev.csv
python run.py eval --answers submissions/benchmark_answers_dev.csv
python run.py bench --out submissions/benchmark_answers.csv      # full submission file
```

Edit `data_dir` in `config.yaml` if the data is not in `../maple_data/maple_collections_release`.

## Repository layout

| Path | Layer | What |
|---|---|---|
| `src/layer1/` | 1 Data Product Factory | source registration, profiling, (next) silver cleaning, identity resolution, C360 |
| `src/layer2/` | 2 Insight and NLP | catalog, SQL guard, free-LLM gateway (fallback, pacing, cache), Q&A pipeline, policy RAG, benchmark runner, evaluation |
| `src/layer3/` | 3 Feature Store | (next) feature definitions shared by training and live scoring |
| `src/layer4/` | 4 Models and Decisioning | (next) uplift NBA, policy gate, explanations |
| `app/` | Agent Desk | (next) Streamlit screens |
| `contracts/` | | data contract YAML for the golden C360 (from DC-COLL-001) |
| `reports/` | | profile, data quality report, benchmark evaluation |
| `submissions/` | | benchmark answers CSV |
| `tests/` | | guard tests, end-to-end mock tests |

## Safety built into Layer 2

- The database is opened **read-only**; the SQL guard allows exactly one SELECT on an allowlist of tables,
  blocks DDL/DML, file-reading functions, other schemas and protected-attribute columns, adds a row limit
  and enforces a timeout (`tests/test_guard.py`).
- Gold answers and labels (`labels/`) are registered in a `hidden` schema that Layer 2 can never query.
  The benchmark runner reads only `question_id`, `question_text` and `as_of_date`.
- Every LLM call, plan, query, answer and refusal is written to `logs/audit.jsonl`.

## What changed from our design (and why)

| Design | Build | Why |
|---|---|---|
| Local models only (Ollama) | Free providers only, through one gateway: our GPU (vLLM, Qwen2.5) + Gemini free tier + Groq free tier, with fallback, pacing and a response cache | No paid APIs; free tiers have rate limits, so the gateway falls back and caches; the GPU model handles bulk work |
| 300 hand-labelled notes | the 500 public labels for notes and transcripts | Provided by organisers; more and independent |
| _add as we go_ | | |

## AI tools we used and for what

| Tool | Used for |
|---|---|
| Qwen2.5 (local, vLLM on our GPU) | NL-to-SQL fallback, text feature labelling of notes/transcripts (runtime) |
| Gemini (Google AI Studio free tier), Groq free tier | NL-to-SQL planning and answer writing (runtime) |
| Claude (chat) and Claude Code | design review and code generation under team review (we read, test and own every change) |
| _add as we go_ | |
