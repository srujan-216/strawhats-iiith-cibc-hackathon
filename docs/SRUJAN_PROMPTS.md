# Srujan — Claude Code prompts (laptop)

You own **Layer 1** (cleaning, identity resolution, C360, data quality report, data contract),
**Layer 2** (Q&A, benchmark answers), the **Agent Desk app** and the **README**.
You develop on samples; Varshith runs your code on full data on the GPU machine.

Before starting: `CLAUDE.md` is in the repo root, the starter repo is pushed, you work on `srujan/*`
branches. LLMs are free only: get a Gemini key (Google AI Studio) and a Groq key, and set the `local`
provider in `config.yaml` to Varshith's Tailscale IP once his vLLM server is up.

## Your schedule (IST)

| When | Task | Hand-off |
|---|---|---|
| 3 Oct, first 2 h | **S0** kickoff, data notes, sample helper | share `docs/DATA_NOTES.md` with Varshith |
| until ~15:00 | **S1** silver cleaning (sample) | push; Varshith runs full silver tonight |
| ~15:00–20:00 | **S2** Layer 2 baseline + evaluation loop | |
| ~20:00–01:00 | **S3** identity resolution (sample) | push by 01:00; Varshith runs full match overnight |
| sleep ~01:00–06:00 | | |
| 4 Oct 06:00–10:00 | **S4** C360, DQ report, contract | pull Varshith's full-run reports |
| 10:00–11:00 | **I** integration (with Varshith, on GPU machine) | |
| 11:00–16:30 | **S5** Layer 2 improvements, **S6** Agent Desk, README | wire `score_case()` from Varshith |
| 16:30–18:30 | demo video and deck together | |
| 19:00–20:15 | **E** extra benchmark questions | ask Varshith to keep vLLM up |
| 20:15–21:00 | **F** final check, push, submit form | |

---

### S0. Kickoff (first 45 minutes)
```
Read CLAUDE.md, then maple_collections_release/README.md and DATA_DICTIONARY.xlsx (data_dir is in
config.yaml). The repo has a starter: run.py, src/layer1/register.py, src/layer1/profile.py and a full
Layer 2 in src/layer2/ (free-LLM gateway, SQL guard, Q&A, benchmark runner) with tests.
1. Run `python run.py register` and `python run.py profile --sample 200000`. Fix register.py if any of
   the 31 tables is not found or loads wrongly (types, NA codes, leading zeros lost in main.*).
2. Write docs/DATA_NOTES.md: customer key column and format for each of the five source systems; NA
   codes and null conventions; date formats per table; where the 500 note/transcript labels are; where
   DC-COLL-001 is; benchmark files, columns and how the dev/test split is marked; where the dictionary
   and the data disagree.
3. Add `--sample N` support (customer-level, seed 42) as a shared helper in src/common/sample.py.
4. Check the gateway: with GEMINI_API_KEY and GROQ_API_KEY set, run
   `python run.py ask "How many open collections cases are there?"` and show which provider answered
   (logs/audit.jsonl). Run `PYTHONPATH=. pytest -q`. Show me DATA_NOTES.md and the outputs, then stop.
```

### S1. Silver cleaning
```
Read CLAUDE.md sections 2, 4, 5, 6 and docs/DATA_NOTES.md. Plan, then build src/layer1/silver.py and
`python run.py silver [--sample N]`. For customers, card_accounts, loan_accounts, deposit_accounts,
collections_cases, contact_history, promises_to_pay, agent_notes, external create silver.<table>:
parse mixed date formats (log unparseable counts), phones to E.164, postal codes to "A1A 1A1", NA codes
to NULL, IDs kept as text with leading zeros, exact duplicates removed, current CDC versions only, latest
snapshot per account, schema drift (e.g. channel vs channel_v2) coalesced and logged.
Every rule writes a row to silver.fix_log(table_name, rule, rows_affected, example_before,
example_after, run_ts). Nothing dropped silently. Big tables in DuckDB SQL, not pandas. Tests for every
normaliser. Develop on --sample 50000; it must also run on full data (Varshith runs it tonight), so keep
memory bounded and print timings.
```

### S2. Layer 2 baseline and evaluation loop
```
Read CLAUDE.md and src/layer2/*. Free LLMs only: route `default` = [gemini, local, groq]. The gateway
caches every response, so reruns cost no quota. Run
`python run.py bench --split dev --out submissions/benchmark_answers_dev.csv --fresh` then
`python run.py eval`. Report accuracy, refusal precision/recall, which provider answered each question,
and the 10 worst failures with the SQL. Group failures by cause (wrong table, wrong metric formula, date
window, formatting, refusal error, retrieval miss). Then fix the biggest cause only, rerun, and report
before/after. Keep prompts small (relevant tables/columns only) so free-tier token limits hold.
Log changes in reports/l2_changelog.md. Never read gold answers, should_refuse, metric_id,
expected_tables or rubrics at runtime; never hard-code answers or question ids.
```

### S3. Identity resolution (develop on sample, Varshith runs full)
```
Plan, then build src/layer1/match.py and `python run.py match [--sample N]`, following CLAUDE.md
section 5. (1) Collapse CRM duplicates. (2) Deterministic links via tables with account id +
crm_customer_id; check whether external.bank_subject_ref equals the deposits key. (3) Splink (DuckDB
backend) on name (+ preferred_name), DOB incl. day/month swap, phone last 10 digits, postal code / FSA,
email; blocking on FSA + birth year and on phone; thresholds >=0.95 merge, 0.70-0.95 steward queue,
<0.70 separate. (4) Precision/recall against deterministic links held out as truth, written to
reports/match_report.md with examples per band. Output id_xref(source_system, source_key, golden_id,
match_method, match_confidence, evidence_json); golden_id stable across reruns.
Make it resumable and memory-safe for 1M+ records; save trained Splink settings to
models/splink_settings.json so the full run reuses them. Test on --sample 50000. Also write
src/layer1/keys.py with to_golden(crm_customer_id) for Varshith.
```

### S4. Golden C360, DQ report, data contract
```
Plan, then build src/layer1/c360.py (`run.py c360`) and src/layer1/dq_report.py (`run.py dq-report`).
c360_customer, c360_account (role primary/joint/co-borrower), c360_case with the survivorship rules in
CLAUDE.md and field_trust (source, refreshed_at, dq_status). Quality checks Q1-Q7 (uniqueness, match
threshold, consent never null -> false, dpd valid vs bucket, open case resolves to one golden_id,
freshness, no protected/proxy columns) into gold.dq_results.
Generate reports/data_quality_report.md from silver.fix_log + gold.dq_results + reports/match_report.md:
one row per issue (table, issue, records affected, how handled). Write contracts/c360_customer.yaml from
DC-COLL-001's structure (owner, schema with types/class/source, quality rules with thresholds, allowed and
prohibited uses, refresh, SLA, lineage, version) and a test that it matches the real columns.
```

### S5. Layer 2 improvements
```
Continue the S2 loop on the current failure causes. Allowed: catalog/table selection, metric matching,
our own few-shot examples (not copied from dev gold), answer formatting to the template, retries,
text_sql for notes/transcripts with note-id citations, policy RAG (current versions, EN/FR). Point Q&A
at the C360 tables now they exist. Add 15 of our own unseen-style questions in tests/l2_holdout.csv and
check we don't regress. Report dev accuracy after each change. If free quotas run low, switch the
default route to [local, gemini, groq] and compare accuracy.
```

### S6. Agent Desk app
```
Build app/streamlit_app.py (`run.py app`), read-only DuckDB, for the demo:
- role picker (agent, supervisor, strategy manager, data steward) using role-based views
- case screen: golden C360 with trust badges, accounts, recent contacts/notes, hardship flag; the NBA
  recommendation from Varshith's score_case(case_id) with three reasons, evidence, confidence, policy
  checks; Accept / Edit / Reject where Edit/Reject require a reason code; decisions written to a separate
  decisions log (the only write the app makes)
- ask box: Layer 2 answer card (answer, understood tokens, SQL/citations, badge, follow-ups)
- supervisor queue (hardship, vulnerable, escalated, low confidence) and steward queue (0.70-0.95 pairs)
Cache queries; every screen under 3 seconds on full data. Then update README: setup with free keys and
the local endpoint, every run.py command, screenshots, "what changed" and "AI tools" rows.
```

### I. Integration (4 Oct ~10:00, on the GPU machine, with Varshith)
```
Run `python run.py all` from a clean clone on full data and fix anything that breaks. Run tests,
`bench --split dev`, `eval`, and open the app. Produce a pass/fail checklist against CLAUDE.md section 8
and the build brief's "must show" per layer. Fix gaps in priority order.
```

### E. Extra benchmark questions (4 Oct, 19:00)
```
New benchmark questions are at <path>. Do not change code that affects answers unless a crash prevents
running. Confirm the local vLLM endpoint and free keys respond. Run
`python run.py bench --questions <path> --out submissions/benchmark_answers_extra.csv`, merge with
submissions/benchmark_answers.csv into one CSV in the template format (every released question exactly
once, refused true/false), validate columns, row count and ids, and commit
"bench: final answers incl. 19:00 set". Do not edit any answer.
```

### F. Final check (4 Oct, 20:15)
```
Verify pass/fail: clean clone runs with the README steps; README has how to run, what changed, AI tools;
docs/architecture.pdf; contracts/c360_customer.yaml; reports/data_quality_report.md generated;
submissions/benchmark_answers.csv complete and valid; no data, keys or .duckdb committed; no paid API
code; tests pass. Fix only trivial issues. Remind us to push before 21:00 IST.
```

### When stuck
```
This is failing: <paste error/output>. Reproduce on --sample 50000, find the root cause, explain it in two
sentences, propose the smallest fix, then apply it with a test.
```
