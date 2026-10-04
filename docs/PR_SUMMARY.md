# Pre-freeze self-review (internal)

Scope: everything merged into `main` since the starter was imported on 2026-10-03. **86 passed, 1 skipped.**
Not for sharing — this is a map so I can answer any judge question in a hurry.

## Layer 1 — Data Product Factory

| File | What |
|---|---|
| `src/layer1/register.py` | Load all 31 source files; honours `schema/schema.json` so text IDs stay text (transcript_id, bureau_file_number no longer load as BIGINT). |
| `src/layer1/silver.py` | Clean, dedupe, parse DOBs (CRM day/month-ambiguous rows keep both readings), pad deposit CIFs to 10 digits, repair DFI-0812 bureau rotation, coalesce `channel_v2` drift (REL-0926), log every rule to `silver.fix_log`. |
| `src/layer1/match.py` | Identity resolution. CRM clusters via `duplicate_of_crm_id` + `national_id_hash`; deterministic bridges via `account_monthly_snapshot` / `coll_customer_ref` / CIF→deposits; Splink dedupe within silver.customers with rule-scorer fallback. `golden_id = min(crm_customer_id)` over live members. |
| `src/layer1/c360.py` | `gold.c360_customer / c360_account / c360_case / field_trust`. Survivorship: consent AND, protective flags OR, contact most-recent-verified. Hash-CTE account build (fixed a 171 GB OOM in correlated subquery form). Seven quality checks Q1–Q7. |
| `src/layer1/dq_report.py` | Rolls up `silver.fix_log` + `gold.dq_results` + match report into one markdown. |
| `contracts/c360_customer.yaml` | Based on DC-COLL-001; 60+ fields with class, survivorship rule, allowed/prohibited uses. Test asserts contract matches the real columns. |

**Numbers to defend.** 1,001,069 customers / 1,633,394 accounts (incl. 896 joint, 212 co_borrower) / 367,229 cases / 3,026,227 field_trust rows / 184,526 → 3,695,875 id_xref rows. Splink recall 0.990, precision 0.414 (floor; see `reports/match_report.md`). DC-COLL-001 orphan rate: 1.00% (right at the limit — call out in demo). All Q1–Q7 pass. Full `python run.py all` runs clean in about an hour on the laptop with 2 GB memory_limit.

Reports: `reports/data_quality_report.md`, `reports/match_report.md`, `reports/silver_fix_log.md`, `reports/profile.md`.

## Layer 2 — Insight and NLP

| File | What |
|---|---|
| `src/layer2/llm.py` | Free-LLM gateway. OpenAI-compatible for Gemini + Groq. Per-provider pacing, 503 retry once after 3 s, waits up to 75 s for the earliest cool-down to recover, SQLite response cache, audit of every call AND every failed attempt. `reasoning_effort` configurable per provider and per purpose (in the cache key). |
| `src/layer2/guard.py` | SQL guard: one SELECT, allowlisted tables, no DDL/DML/file functions/protected columns, row limit, timeout. 7 tests. |
| `src/layer2/catalog.py` | Visible tables, columns, metrics, protected list. Shrunk plan prompt to 3 tables × 25 columns × 60-char descriptions so Groq's 8k/min fits. |
| `src/layer2/qa.py` | Rule-scope → plan → guard → execute → answer, with hardened grounding: zero rows → "I don't have data for that" + SQL shown; zero docs → refuse "no current policy covers this"; retry exhausted → refuse with last error; every non-refusal answer must carry `sql_or_sources` + `reasoning` + certified/exploratory badge. |
| `src/layer2/benchmark.py` | Runs the system on every question; writes a `.timing.csv` sidecar; cp1252-safe log line. |
| `src/layer2/evaluate.py` | Dev-only scoring. Table answers checked value-by-value within each question's tolerance; refusals detected by "Refuse…"; text answers listed for manual review. |
| `src/layer2/rag_docs.py` | BM25 over current-version policy docs. |

**Config:** `gemini-3.5-flash` with `reasoning_effort: {plan: medium, sql_fix: medium, answer: low, answer_docs: low}`, Groq `openai/gpt-oss-120b` as fallback (comparison in `reports/l2_effort_comparison.md`; A/B/C ran, C chosen).

**Dev bench (14 scored):** 4/14 accuracy (28.6%), refusal_accuracy / recall / precision all 1.00. Score is low — text/document questions aren't auto-scored and SQL questions mostly return partial values. Grounding guardrails are the demo talking point here (refusal of BQ-024 FSA, BQ-031 gender).

## Layer 3 — Feature store + text classifier

| File | What |
|---|---|
| `src/layer3/catalog.yaml` | 23 features (16 numeric + 7 text-derived) with name, entity, type, recipe, sources, refresh, why. Three features noted "low proxy signal; retain for P6 training". Protected list is listed as *excluded*. |
| `src/layer3/features.py` | Single-SQL build of `gold.features_offline` and `features_online`; the SAME expression per feature across both. 23 cols × 1,001,069 rows in 12 s on full data. |
| `src/layer3/text_classifier.py` | TF-IDF (word + char n-grams) + logistic regression on 500 note labels and 500 transcript labels. Scored 760,594 notes + 25,000 transcripts to `gold.text_features_*`. |
| `src/layer3/feature_report.py` | Coverage + corr with cured proxy + |r|>0.9 pair prune. All 23 kept pending P6 selector. |
| `tests/test_feature_parity.py` | 1,000-key check that `features_offline(decision_date=today) == features_online`. Must stay green. |

Reports: `reports/text_feature_eval.md` (per-field F1 incl. vulnerability caveat), `reports/feature_report.md`.

**Vulnerability survivorship:** `vulnerability_signal = structured_vulnerability_flag OR (classifier_true AND confidence > 0.8)`. Documented as "classifier only tips to true, never false." 62,683 of 1,001,069 customers (6.3%) tip to true.

## Layer 4 — NBA + policy gate + explanations

| File | What |
|---|---|
| `src/layer4/randomisation.py` | Pre-flight SMD check: `no_contact_holdout` vs `champion` on `assignment_method='random'`. Worst |SMD| = 0.033. Segment breakdown shows the 71.5% holdout cure is uniform, not driven by one easy segment. |
| `src/layer4/nba.py` | Six LightGBM T-learners (one per action). Trained in 13 s on 175k randomised rows. AUCs 0.93–0.98. Decision rule: `argmax p_cure(a) * balance_at_risk - action_cost(a)`. `score_case()` 148–190 ms end-to-end. |
| `src/layer4/policy_gate.py` | 8 rules (insolvency, deceased, cease-contact, dispute, third-party rep, contact cap, hardship-never-harsher, 90+ no-hardship). Per-row and vectorised versions must agree. 11 tests. |
| `src/layer4/explain.py` | SHAP top-3 positive contributors mapped to plain-English templates. LLM never writes explanations (CLAUDE.md §5). |

Reports: `reports/randomisation_check.md`, `reports/model_card.md`.

**Live scoring:** 83,677 open cases scored in 15 s → `gold.nba_recommendations`. Action mix: digital_nudge 42% / call_best_time 35% / no_contact 9% / escalate 7% / hardship_referral 7% / payment_plan 1%.

**Honesty note (in model card):** `payment_plan`, `hardship_referral`, `escalate` are observational, not randomised; uplift column reports them but they aren't the decision driver. For a plain 30-day-cure target the uplift is small because self-cure is ~71.5%; the real value from the system is `action_cost=0 for no_contact`, which stops wasting dials on customers who were going to self-cure.

## Agent Desk — Streamlit app

`app/streamlit_app.py`. Read-only DuckDB, cached. Hero case `CS-2026-134197` (golden_id `JAR-2837`) opens by default. Decisions log is append-only `warehouse/decisions.parquet`; the app never writes to DuckDB. Screenshots in `docs/screenshots/`.

Screens: case + ask + supervisor queue + steward queue. Role picker (agent / supervisor / manager) in sidebar. Score-case latency on real cases: 148–190 ms.

## Governance

`src/governance/fairness.py` — the only `src/` reader of protected columns. Measures action distribution, predicted cure, and vulnerability_signal rate per group over 5 attributes (gender, marital, citizenship, age_band, newcomer). 5 pp fairness band. **All groups within the band on predicted cure.**

`tests/test_no_protected_features.py` — three guards: catalog has no protected feature names; `gold.features_online` has none; no `src/` file outside `governance/` references the names (allowlist for `src/layer2/catalog.py` and `src/layer3/feature_report.py`, which legitimately list them to BLOCK them).

Report: `reports/fairness_report.md`. Model card has a Fairness section appended.

## Tests at a glance (86 passed, 1 skipped)

- Gateway (fallback, cache, 503 retry, failure audit, per-purpose reasoning_effort, wait-for-cooldown, Echo helper)
- Guard (one SELECT, no DDL, no forbidden tables, …)
- Silver rules (phone / postal / email / province / CIF / CRM DOB / DFI-0812 / contact drift / dedupe / note placeholders) — 27 tests
- Sample helper determinism and nesting
- Evaluate (gold table parse, tolerances, refusal detection)
- QA grounding (zero rows / zero docs / retry exhausted / badge required / certified vs exploratory)
- Catalog shrink (schema_block fits, table default k=3)
- Match (CRM clusters, golden_id live-first, deterministic bridges, stable across reruns)
- C360 contract matches gold columns
- Feature parity (1,000 keys offline == online)
- Policy gate (one test per rule + vectorised match + hardship-never-harsher)
- No protected features (catalog, features_online, src/ scan)
- The one skip is `test_qa_mock` which only runs with `FAKE_CONFIG` set

## Things I want to tell the judges proactively

1. **DC-COLL-001 orphan contact rate is 1.00% — right at the policy threshold.** It passes, but barely. Mentioned in the DQ report.
2. **DFI-0812 is repaired, not quarantined.** 9,918 rows had the four inquiry columns rotated one place right. Rule: `inquiries_hard_3m > inquiries_hard_6m` can never hold in clean data. Rotating back yields consistent values and the original is kept in `dfi0812_as_loaded` for audit.
3. **Splink precision 0.414 is a floor,** not a verdict. CRM-known duplicates are the only ground truth available locally; the gap between recall (0.990) and precision suggests the system is finding real duplicates the CRM never recorded. Steward queue carries 1,331 pairs for review.
4. **The uplift story needs careful framing.** No-contact holdout cures at 71.5%; champion at 72.8%. Uplift is 1–2 pp on average, which is accurate. The system still saves money because it stops dialling customers who were going to self-cure.
5. **The free-LLM gateway cannot be the critical path for every answer.** We cache every response, retry 503s, and wait up to 75 s for a cool-down. The audit log shows which provider actually answered.

## Pending (held per plan)

- P10 extra benchmark questions, 19:00 IST — explicitly deferred.
- Final check, 20:15 IST.
