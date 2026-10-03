# Identity resolution report
Snapshot: 2026-10-03 22:22:55
Sample: N=full customers
Probabilistic method: **splink** (splink falls back to rules if training fails)

## Probabilistic matcher vs deterministic truth (CRM pointer + national_id_hash)
- Truth pairs: 18,928
- Predicted (any band): 27,844
- True positives: 18,742
- **Recall**: 0.990 (of known CRM duplicates found)
- **Precision**: 0.673 (floor only: non-truth predictions include real duplicates the CRM did not record, so true precision is higher - needs manual spot-checks)

## Coverage by source
| source      | keys linked / total   | coverage %   | deterministic %   |
|-------------|-----------------------|--------------|-------------------|
| cards       | 584,725/660,000       | 88.6%        | 88.6%             |
| collections | 356,864/367,229       | 97.2%        | 97.2%             |
| crm         | 1,020,000/1,020,000   | 100.0%       | 100.0%            |
| deposits    | 686,725/780,000       | 88.0%        | 88.0%             |
| external    | 514,407/1,000,000     | 51.4%        | 51.4%             |
| loans       | 360,836/404,500       | 89.2%        | 89.2%             |

### Bridge-coverage warnings

- **cards**: deterministic coverage 88.6% - fix the bridge, do not paper over with Splink
- **deposits**: deterministic coverage 88.0% - fix the bridge, do not paper over with Splink
- **external**: deterministic coverage 51.4% - fix the bridge, do not paper over with Splink
- **loans**: deterministic coverage 89.2% - fix the bridge, do not paper over with Splink

## Example pairs per band

### merge (>=0.95)

| crm_a    | crm_b    |   probability |
|----------|----------|---------------|
| DOW-3993 | DOW-9053 |             1 |
| ANH-6662 | ANH-7962 |             1 |
| ISM-2725 | ISM-7105 |             1 |
| PHW-7379 | PHW-9379 |             1 |
| KAS-2306 | KAS-9526 |             1 |

### steward (0.70-0.95)

| crm_a    | crm_b    |   probability |
|----------|----------|---------------|
| ADB-2218 | HEB-2358 |          0.95 |
| AMB-5162 | JAB-4985 |          0.95 |
| PRC-2912 | RIC-5601 |          0.95 |
| JAM-6711 | MAM-6980 |          0.95 |
| GRG-3270 | JOG-7135 |          0.95 |
