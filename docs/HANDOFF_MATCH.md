# Handoff: identity resolution (S3), for Varshith

Status 2026-10-03: `python run.py match --sample 50000` finished in 42 s on Srujan's laptop with
Splink 5.0 as the probabilistic matcher. Full-data run (1 M customers) belongs to the GPU workstation.

## What you run

```bash
git pull                                  # srujan/match merged to main
pip install -r requirements.txt           # adds splink>=5.0
python run.py register                    # if warehouse/maple.duckdb is stale
python run.py silver                      # if silver.* is stale
python run.py match                       # full data; writes silver.id_xref + reports/match_report.md
```

- Memory: `config.yaml` → `silver.memory_limit` applies here too; raise to `16GB`+ on the workstation.
- Resumable: `models/splink_settings.json` is saved by the first run; subsequent runs with the same
  silver.* data reuse it. Delete the file to retrain.
- If Splink training fails (OOM, library issue), the code auto-falls-back to a **rule-based scorer**
  that uses the same thresholds (≥0.95 merge, 0.70–0.95 steward) and writes the same `silver.id_xref`
  schema. The report prints which path was used.

## What it produces

- **silver.id_xref** — `(source_system, source_key, golden_id, match_method, match_confidence, evidence_json)`
  - one row per source key for `cards`, `loans`, `deposits`, `collections`, `external`, `crm`
  - `match_method`: `crm_identity | bridge_ams | bridge_coll | bridge_cif`
  - `match_confidence = 1.0` on this release (every row is deterministic once Splink merges
    into the CRM clusters)
  - `golden_id = min(crm_customer_id)` across the cluster's live members; falls back to the overall
    min if every member is deleted. Stable across reruns.
- **silver.steward_queue** — `(crm_a, crm_b, match_probability)` for pairs in `0.70–0.95`
- **models/splink_settings.json** — trained Splink model (safe to commit; small, no PII)
- **reports/match_report.md** — precision/recall vs CRM-known duplicates and coverage per source

## Using golden_id downstream (feature store, C360)

In Layer 3/4 code, go through `silver.id_xref`:

```sql
SELECT x.golden_id, ca.*
FROM silver.card_accounts ca
JOIN silver.id_xref x ON x.source_system='cards' AND x.source_key = ca.card_account_id
```

For CRM, use `(source_system='crm', source_key=crm_customer_id)`. For the ex-dupe CRM records
that CRM did not mark, the join still works — `crm_customer_id` is the source key.

Users build their own `c360_customer` from this. There is **no** `src/layer1/keys.py` helper
file; cut from scope.

## Sample run numbers (N=50,000 customers)

| Metric | Value |
|---|---|
| Runtime | 42 s |
| id_xref rows | 184,526 |
| Multi-member CRM clusters | ~900 |
| Probabilistic candidate pairs | 756 |
| Recall vs CRM-known duplicates | **0.997** |
| Precision vs CRM-known duplicates | **0.414** (floor — non-truth predictions include real duplicates CRM did not record) |
| Deterministic coverage per source | cards/loans/collections/crm 100%; deposits 92%; external 90% |

The precision is a floor only. Splink finds many pairs the CRM never recorded, most of which are
likely real duplicates. Spot-check a few `steward_queue` rows during the demo.

## Known gaps / future work

- **Deposits 92%, external 90% deterministic coverage.** The deposit→ams bridge is missing on
  deposit accounts with no monthly snapshot (closed before the snapshot window). We flag this
  but do not try to fill it probabilistically — fixing the bridge belongs upstream.
- **Splink training warnings** on 50k ("some m values not trained") are expected: there are few
  known duplicates in the sample, so some comparison levels never fire. On the full data they will
  mostly disappear; the warnings are logged, not errors.
- **No steward UI.** `silver.steward_queue` is just a table view, per the scope cut in CLAUDE.md §8.
