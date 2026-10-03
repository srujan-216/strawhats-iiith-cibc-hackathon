# Identity resolution report
Snapshot: 2026-10-03 21:02:18
Sample: N=50000 (silver.* sample)
Probabilistic method: **splink** (splink falls back to rules if training fails)

## Probabilistic matcher vs deterministic truth (CRM pointer + national_id_hash)
- Truth pairs: 314
- Predicted (any band): 756
- True positives: 313
- **Recall**: 0.997 (of known CRM duplicates found)
- **Precision**: 0.414 (floor only: non-truth predictions include real duplicates the CRM did not record, so true precision is higher - needs manual spot-checks)

## Coverage by source
| source      | keys linked / total   | coverage %   | deterministic %   |
|-------------|-----------------------|--------------|-------------------|
| cards       | 29,636/29,636         | 100.0%       | 100.0%            |
| collections | 17,517/17,517         | 100.0%       | 100.0%            |
| crm         | 50,287/50,287         | 100.0%       | 100.0%            |
| deposits    | 34,484/37,482         | 92.0%        | 92.0%             |
| external    | 25,980/28,805         | 90.2%        | 90.2%             |
| loans       | 18,118/18,118         | 100.0%       | 100.0%            |

## Example pairs per band

### merge (>=0.95)

| crm_a    | crm_b    |   probability |
|----------|----------|---------------|
| RYB-2589 | RYB-8649 |             1 |
| WHB-3283 | WHB-5423 |             1 |
| LEA-5964 | LEA-6284 |             1 |
| KUB-3768 | KUB-5388 |             1 |
| TRP-3119 | TRP-8159 |             1 |

### steward (0.70-0.95)

| crm_a    | crm_b    |   probability |
|----------|----------|---------------|
| AMN-4574 | CAN-9694 |         0.939 |
| DAB-7681 | DAK-5585 |         0.939 |
| JEN-3295 | PIN-3055 |         0.939 |
| BEG-5264 | BEP-3359 |         0.937 |
| LIS-9794 | LIW-8224 |         0.937 |
