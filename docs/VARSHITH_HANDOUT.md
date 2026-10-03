# Varshith — Build Phase Handout

**Team Straw Hats · CIBC Collections Hackathon · Deadline 4 Oct 2026, 21:00 IST (commits after that don't count)**

This handout is everything you need: your role, machine setup, schedule, every deliverable with its
"done when" check, hand-offs with Srujan, and the exact Claude Code prompts to paste.

---

## 1. Your role in one paragraph

You own **Layer 3 (Feature Store)** and **Layer 4 (Models and Decisioning)**, which is our Next Best
Action (NBA) use case, the part the brief says to build in depth. You also own the **governance
reports** (fairness, monitoring, model card). Because you have the GPU machine, you also **run every
heavy job**: the local LLM server for the whole team, LLM labelling of notes, full-data runs of
Srujan's Layer 1 code, and model training. Srujan owns Layer 1, Layer 2, the app and the README.

**Rule of thumb:** if it is slow, big or needs the GPU, it runs on your machine.

---

## 2. Rules you must follow (from CLAUDE.md)

1. **Free LLMs only.** No paid APIs. You serve a local model on your GPU (unlimited). Gemini and Groq
   free tiers are only for Q&A, never for bulk jobs.
2. **No protected attributes or proxies in any feature, model, rule or decision:** gender, marital
   status, citizenship, household/dependants, newcomer, accessibility, vulnerability type, accent, voice
   pitch, age/age band, CPP/OAS and CCB deposit flags, FSA income fields, majority language. Only
   `src/governance/fairness.py` may read them, to measure gaps.
3. **Outcome columns are labels, never features:** `cure_flag`, `days_to_cure`, `outcome`, `dpd_at_day_*`,
   `overdue_at_day_*`, `roll_forward_count`, `nba_accepted_flag`, `human_override_flag`, and anything
   dated after the decision date.
4. **Every recommendation has a plain-English reason** (top 3 reasons + evidence + confidence).
5. **A human decides.** The model recommends; the agent accepts, edits or rejects. Hardship, vulnerable,
   escalated and low-confidence cases go to a supervisor first.
6. **Hardship protects, never penalises.** It can only lead to supportive actions.
7. **Never commit data, DuckDB files, caches, model files over 50 MB, or keys.**
8. **Commit small and often on `varshith/*` branches**, merge to `main` by PR every few hours. Your
   commits are half of our team-work evidence.

---

## 3. Setup (first 2 hours) — what "ready" looks like

| Item | Done when |
|---|---|
| Data | release zip + voice zip downloaded and unzipped (~16 GB); path set in `config.yaml` |
| Python env | `requirements.txt` + torch (CUDA), sentence-transformers, faster-whisper, lightgbm, shap, scikit-learn installed; `torch.cuda.is_available()` is True |
| Local LLM server | vLLM (Linux) or Ollama (Windows/Mac) serving one Qwen model on port 8000 (OpenAI-compatible) |
| Shared with Srujan | Tailscale installed on both machines; Srujan can call `http://<your-tailscale-ip>:8000/v1/models` |
| Smoke test | `scripts/smoke_gpu.py` prints timings for one LLM call, one embedding batch, one Whisper file |
| Full data loaded | `python run.py register` and `profile` done on full data; `reports/profile.md` committed |

**Which model to serve (check `nvidia-smi` for VRAM):**

| VRAM | Serve | Command |
|---|---|---|
| 24 GB or more | Qwen2.5-14B-Instruct-AWQ | `vllm serve Qwen/Qwen2.5-14B-Instruct-AWQ --host 0.0.0.0 --port 8000 --max-model-len 16384 --gpu-memory-utilization 0.85` |
| 12–16 GB | Qwen2.5-7B-Instruct | `vllm serve Qwen/Qwen2.5-7B-Instruct --host 0.0.0.0 --port 8000 --max-model-len 16384` |
| Windows / no vLLM | Ollama | `ollama pull qwen2.5:14b` (or `:7b`), base_url `http://localhost:11434/v1`, model `qwen2.5:14b` |

Set the `local` provider's `model` in `config.yaml` to exactly the name you serve. One model serves
both SQL questions and note labelling. Keep the server running in `tmux` all through the build,
especially **4 Oct 19:00–20:15** when the extra benchmark questions run.

---

## 4. Your schedule (IST)

| When | Task | GPU / long jobs running | Hand-off |
|---|---|---|---|
| 3 Oct, first 2 h | **V0** setup, LLM server, Tailscale, full data | download, register | send Srujan your Tailscale IP + model name |
| until ~15:00 | **V1** structured features + feature store | full profile | |
| ~15:00–20:00 | **V2** text features: prompt, eval on 500+500 labels | start ~20k labelling job | |
| ~20:00–01:00 | **V3** randomisation check, uplift model, **V4a** policy gate | labelling continues | |
| ~01:00–03:00 | **R1** full runs of Srujan's silver + match; start overnight jobs | full silver, full match, student scoring of 1.5M notes, full feature build | push generated reports |
| sleep ~03:00–08:00 | | overnight jobs | |
| 4 Oct 08:00–10:00 | **V4b** explanations, `score_case()`, batch scoring; retrain on full features | training | give Srujan `score_case()` |
| 10:00–11:00 | **I** integration with Srujan (your machine) | `run.py all` | |
| 11:00–16:30 | **V5** governance reports, model card; help wire the app; voice features if GPU free | full rerun | |
| 16:30–18:30 | demo video + deck with Srujan (your part below) | | |
| 19:00–20:15 | keep LLM server up; support extra benchmark run | | |
| 20:15–21:00 | final push of your branch and reports | | |

---

## 5. Deliverables and "done when"

| # | Deliverable | Path | Done when |
|---|---|---|---|
| D1 | Local LLM endpoint + setup notes | `docs/gpu_setup.md`, `scripts/smoke_gpu.py` | Srujan's gateway answers a question through `local` |
| D2 | Structured feature store | `src/layer3/features.py`, `src/layer3/store.py` | offline (point-in-time) and online built from the same definitions; parity test passes |
| D3 | Feature catalog + selection report | `src/layer3/catalog.yaml`, `reports/feature_report.md` | every feature has name, entity, type, meaning, recipe, sources, refresh, owner, version, why; IV, correlation, PSI, proxy check shown |
| D4 | Text (and voice) features | `src/layer3/text_features.py`, `prompts/text_features_v1.txt`, `reports/text_feature_eval.md` | precision/recall/F1 per field on the 500 note + 500 transcript labels; all notes scored |
| D5 | NBA uplift model | `src/layer4/train.py`, `models/`, `reports/model_card.md` | randomisation check, Qini/AUUC, calibration, uplift by decile and segment reported; fallback stated if used |
| D6 | Policy gate | `src/layer4/policy_gate.py`, `tests/test_policy_gate.py` | every rule unit-tested, including "hardship never leads to a harsher action" |
| D7 | Explanations + scoring | `src/layer4/explain.py`, `src/layer4/score.py` | `score_case(case_id)` returns action, 3 plain-English reasons with evidence, confidence, checks passed, in under 1 s; all open cases in `gold.nba_recommendations` |
| D8 | Governance reports | `src/governance/fairness.py`, `reports/fairness_report.md`, `reports/monitoring.md`, `tests/test_no_protected_features.py` | gaps by protected group reported; test proves no protected/proxy column is a model input |
| D9 | Full-data runs | generated `reports/data_quality_report.md`, `reports/match_report.md` | Srujan's Layer 1 ran on full data on your machine and reports are pushed |
| D10 | README rows | `README.md` | Layer 3/4 lines added under "What changed" and "AI tools" |
| D11 | Demo + deck | outside repo | your 90-second demo segment and 3 slides are ready |

**`run.py` commands you add:** `features`, `text-features`, `train`, `score [--case-id X]`,
`governance`, and your steps inside `run.py all`.

---

## 6. Claude Code prompts (paste in order, plan mode first)

### V0. GPU setup and shared LLM server
```
Read CLAUDE.md and docs/DATA_NOTES.md (if it exists yet). This is the GPU machine. Check nvidia-smi
and VRAM. Install requirements plus torch with CUDA, sentence-transformers, faster-whisper, lightgbm,
shap, scikit-learn. Help me start a vLLM (or Ollama on Windows) OpenAI-compatible server on port 8000
with the Qwen model that fits VRAM (see table in docs/VARSHITH_HANDOUT.md), bound to 0.0.0.0, inside
tmux. Set the `local` provider in config.yaml to that model name. Write docs/gpu_setup.md (exact
commands, model, VRAM, how Srujan connects over Tailscale) and scripts/smoke_gpu.py that times one LLM
call through src/layer2/llm.py (route bulk), one embedding batch on cuda, and one Whisper transcription
if voice files exist. Then run `python run.py register` and `python run.py profile` on the full data and
commit reports/profile.md. Do not commit data or models.
```

### V1. Structured features and feature store
```
Read CLAUDE.md sections 4-6. Plan, then build src/layer3/features.py, src/layer3/store.py and
src/layer3/catalog.yaml. Each feature is ONE SQL template plus a catalog entry (name, entity, type,
meaning, recipe, sources, refresh, owner, version, why). The same definition serves:
- build_offline(decision_dates): point-in-time training table using only data before each decision date
- refresh_online() / get_online(keys): latest values in an online DuckDB table
Key by case_id and crm_customer_id from main.* / silver.* now; switch to golden_id later through
src/layer1/keys.py (one function call, no rewrite).
Features: dpd level, dpd 3-month slope, worst dpd 12m, broken promises 90d, promise-due vs expected
payday gap, payroll delay days, salary change 3m, NSF count 3m, cash-flow slope 6m, utilisation trend
6m, bureau score delta 90d, off-us delinquent trades, answer rate 30d, best time band, contacts last 7
days, balance at risk. Never use outcome columns or protected/proxy columns.
Scan heavy history tables (loan_instalments, transactions, card_statements) by year in DuckDB and cache
parts under warehouse/cache/features/ so reruns skip finished parts.
Add `run.py features`, a parity test (1,000 keys: offline at latest date == online), and
reports/feature_report.md (IV/WoE, correlation > 0.9 pruned, PSI < 0.2 across months, kept list with
reasons). Show me the report.
```

### V2. Text features on the GPU
```
Build src/layer3/text_features.py and prompts/text_features_v1.txt. Extract from agent notes and call
transcripts (English and French): hardship_signal (yes/no), delay_reason (job loss, reduced hours,
illness, family, dispute, forgot, other, none), ptp_intent_strength (low/medium/high),
call_sentiment (negative/neutral/positive). Use the gateway with route `bulk` (local GPU only), batched
and concurrent requests to vLLM, JSON output, results cached in warehouse/cache/text_llm/.
1. Measure precision/recall/F1 per field on the 500 public note labels and the 500 transcript labels;
   write reports/text_feature_eval.md with a confusion matrix per field and 5 error examples.
   Iterate the prompt (v1 -> v2) only on a 300-label dev part and report final numbers on the other 200.
2. Label a stratified sample of ~20,000 notes/transcripts (by product, bucket, language) as a resumable
   overnight job with progress in logs/text_llm.log.
3. Train a student classifier on the LLM labels (multilingual-e5-small embeddings on cuda + logistic
   regression; TF-IDF + LR if faster) and score all ~1.5M notes. Report student vs LLM agreement and
   student F1 on the public labels.
4. Record prompt version, model, and accuracy in catalog.yaml; add the text features to the store.
Add `run.py text-features [--stage eval|label|train|score]`.
```

### V3. NBA uplift model
```
Plan, then build src/layer4/train.py and `run.py train`.
1. Randomisation check: are treatments assigned at random within test_cell? Compare feature balance
   (standardised mean differences) across cells and report.
2. Decision point = case open / review date; target = cure within 30 days after it. Map treatment codes
   to our six actions: no_contact, digital_nudge (SMS/email pay link), call_best_time, payment_plan,
   hardship_referral, escalate (escalate is recommend-only).
3. T-learner: one LightGBM classifier per action on randomised cases, time-based train/validation/test
   split, fixed seed. Report Qini/AUUC, calibration plot data, uplift by decile, and results by segment
   and product. If randomisation is weak, train per-action propensity models instead and state it.
4. Decision: argmax over actions of (p_a - p_no_contact) * balance_at_risk - cost_a, respecting daily
   channel capacity from channel_capacity (cost from contact_cost_cad where available).
Save models and metrics to models/ (small files only) and write reports/model_card.md (data, target,
features, metrics, limits, intended use, human review points).
```

### V4a. Policy gate
```
Build src/layer4/policy_gate.py: a list of rules, each a function returning (allowed, rule_id, reason)
for a proposed action on a case. Rules: insolvency (bankruptcy_flag, consumer_proposal_flag,
insolvency_hold_flag) or deceased -> no collection contact, route to specialist; cease-communication or
open dispute -> no contact; credit counselling / third-party representative -> contact representative
only; channel consent per channel; contact cap (contacts_last_7d vs contact_cap_7d); permitted hours in
the customer's time zone; hardship -> only no_contact, digital_nudge with support message,
payment_plan or hardship_referral, plus hardship_programs eligibility; vulnerable -> certified agent and
supervisor queue. If the model's top action is blocked, take the next best allowed action and record
why. Write tests/test_policy_gate.py with one test per rule and a property test that hardship never gets
a harsher action than without hardship.
```

### V4b. Explanations and scoring
```
Build src/layer4/explain.py and src/layer4/score.py with `run.py score [--case-id X]`.
score_case(case_id) -> {action, channel, time_band, reasons[3], evidence, confidence, checks_passed,
blocked_actions, route_to_supervisor, model_version, feature_version}. Online features only. SHAP values
for the chosen action's model -> top 3 drivers -> fixed plain-English templates (one template per
feature, e.g. "Salary credit is {payroll_delay_days} days late"), with evidence ids (note id, policy
section from hardship_programs/reference_documents). No LLM writes explanations. Under 1 second per
case. Batch-score all open cases into gold.nba_recommendations. Tests for templates and for
route_to_supervisor on hardship/vulnerable/low-confidence cases. Give Srujan a 5-line usage example.
```

### V5. Governance reports
```
Build src/governance/fairness.py (the only module allowed to read protected attributes) and
`run.py governance`. Report, by each protected group: recommendation mix, predicted cure, share routed
to supportive actions, and (from the decisions log when available) override rates; flag gaps above a
set threshold. Write reports/fairness_report.md and reports/monitoring.md (DQ results summary, feature
PSI, model calibration, acceptance/override rates by reason and segment). Add
tests/test_no_protected_features.py proving no feature/model input is on the protected or proxy list.
Add fairness results to reports/model_card.md.
```

### V6. Voice features (only if GPU time is free after V5)
```
Run faster-whisper (cuda, float16) on the 2,000 WAVs that lack a transcript or to verify ASR quality,
then compute talk_ratio and silence_ratio per call from turn timings. Do not compute pitch, accent or
any voice-biometric feature. Add them to the store with catalog entries and report coverage.
```

### R1. Full-data runs of Srujan's Layer 1 (night of 3 Oct)
```
Pull main. Run on full data, in tmux, logging to logs/: `python run.py silver`, then
`python run.py match` (reuse models/splink_settings.json), then `python run.py c360` and
`python run.py dq-report` when Srujan has pushed them. Watch memory; if a step fails, fix only what is
needed to run at full size (chunking, memory limits via PRAGMA memory_limit), commit the fix with a
clear message, and note it for Srujan. Commit the generated reports (match_report.md,
data_quality_report.md), not the data.
```

### When stuck
```
This is failing: <paste error/output>. Reproduce on --sample 50000, find the root cause, explain it in two
sentences, propose the smallest fix, then apply it with a test.
```

---

## 7. Hand-offs with Srujan

| You give Srujan | When | You need from Srujan | When |
|---|---|---|---|
| Tailscale IP + model name for the `local` provider | end of V0 | `docs/DATA_NOTES.md` | end of his S0 |
| `score_case()` + usage example | 4 Oct ~10:00 | silver/match code pushed (sample-tested) | 3 Oct ~01:00 |
| generated match + DQ reports from full runs | 4 Oct morning | `src/layer1/keys.py` (`to_golden`) | with match code |
| uptime of the LLM server | always, especially 19:00–20:15 | app screen that shows your recommendation | 4 Oct afternoon |

---

## 8. Your part of the demo and deck

**Demo (about 90 seconds):** open a real hardship case in the app → show the recommended action, the
three reasons with evidence (note id, payroll delay), the policy checks passed, and that a harsher
action was blocked → the agent overrides with a reason code → show the decision in the log and the
fairness report line for that segment.

**Deck (3 slides):**
1. Feature store: one definition for training and live scoring, with structured and text features and the
   parity test.
2. NBA model: why uplift (don't call people who'd pay anyway), randomisation check, Qini result.
3. Explanations and safety: reason card, policy gate rules, human review points, fairness gaps.

---

## 9. Final checklist (tick before 20:45 on 4 Oct)

- [ ] D1–D10 done and pushed; tests pass (`PYTHONPATH=. pytest -q`)
- [ ] `python run.py all` works on full data on your machine
- [ ] No protected/proxy column in any feature or model input (test passes)
- [ ] No paid API code, no keys, no data, no big model files committed
- [ ] LLM server still up for the final benchmark run
- [ ] README has your "What changed" and "AI tools" rows
- [ ] Last commit pushed before **21:00 IST**
