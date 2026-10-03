"""Layer 1, step 2: identity resolution. Links every source key to one golden_id.

  python run.py match [--sample N]

Four passes, in order:

1. CRM clusters: group CRM records that are the same person using
   (a) the CRM's own `duplicate_of_crm_id` pointer and
   (b) the salted `national_id_hash` (dominant signal — ~3x more pairs than the pointer).
   Clusters are the connected components over those two edges.

2. Deterministic bridges: use links the data already carries. We never guess here (match_confidence = 1.0):
   - `account_monthly_snapshot(account_id, crm_customer_id)` bridges every product's natural key
     (card_account_id / loan_id / deposit_account_id) to a CRM record.
   - `collections_cases.coll_customer_ref` is a CRM id copied at case open.
   - `external.bank_subject_ref` = 10-digit CIF; we route it through silver.deposit_accounts
     (CIF already padded in silver) back to CRM.

3. Probabilistic (Splink) within silver.customers to catch same-person pairs that the CRM did not record
   and whose national_id_hash is missing. Blocked by FSA + birth-year and by phone-last-10, trained on an
   N-row sample for speed. Thresholds: >=0.95 auto-merge, 0.70-0.95 steward queue, <0.70 separate.
   If Splink raises or runs out of memory, we fall back to the rule scorer below (same thresholds,
   same id_xref schema). Settings are saved to models/splink_settings.json so the full-data run reuses them.

4. Assemble `silver.id_xref(source_system, source_key, golden_id, match_method, match_confidence,
   evidence_json)`. Within every cluster, golden_id = min(crm_customer_id) over the cluster's live
   records (cdc_operation != 'D'); if the cluster is all-deleted, min of all. Deleted CRM records still
   get a golden_id so historical source links resolve.

Precision/recall of Splink is measured against the deterministic truth above and written to
`reports/match_report.md`, together with per-source coverage and the method mix per source.
"""
from __future__ import annotations
import json, time
from pathlib import Path
import duckdb
from src.common.sample import build_sample, sample_filter

# Splink thresholds (CLAUDE.md section 5)
AUTO_MERGE = 0.95
STEWARD_LOW = 0.70

# Account-product mapping in account_monthly_snapshot (checked against data)
AMS_PRODUCT_TO_SOURCE = {
    "card": "cards",
    "personal_loan": "loans", "auto_loan": "loans", "mortgage": "loans",
    "unsecured_loc": "loans", "student_loc": "loans",
    "chequing": "deposits", "savings": "deposits", "tfsa_savings": "deposits", "usd_account": "deposits",
}


# ------------------------------------------------------------------------------------------- clusters
def build_crm_clusters(con, sample_n: int | None, log=print) -> int:
    """Union-find over (duplicate_of_crm_id) and (shared national_id_hash) edges within silver.customers,
    restricted to the sample. Writes TEMP table crm_clusters(crm_customer_id, cluster_id) where
    cluster_id = min(crm_customer_id) across the cluster's live members (deleted-only clusters fall back
    to overall min). Returns number of multi-member clusters."""
    t0 = time.time()
    filt = sample_filter("customers", "c", n=sample_n)
    con.execute(f"""CREATE OR REPLACE TEMP TABLE _edges AS
        SELECT c.crm_customer_id AS a, c.duplicate_of_crm_id AS b
          FROM silver.customers c WHERE c.duplicate_of_crm_id IS NOT NULL AND {filt}
            AND c.duplicate_of_crm_id IN (SELECT crm_customer_id FROM silver.customers x
                                          WHERE {sample_filter('customers', 'x', n=sample_n)})
        UNION
        SELECT a.crm_customer_id, b.crm_customer_id FROM silver.customers a
          JOIN silver.customers b
            ON a.national_id_hash = b.national_id_hash AND a.crm_customer_id < b.crm_customer_id
         WHERE a.national_id_hash IS NOT NULL
           AND {sample_filter('customers', 'a', n=sample_n)}
           AND {sample_filter('customers', 'b', n=sample_n)}""")
    # iterative connected components in SQL: at each step, every node adopts min(itself, neighbours).
    con.execute(f"""CREATE OR REPLACE TEMP TABLE _nodes AS
        SELECT crm_customer_id AS node, crm_customer_id AS root, (cdc_operation = 'D') AS deleted
        FROM silver.customers c WHERE {filt}""")
    for _ in range(20):   # 20 rounds is enough for any realistic cluster depth
        changed = con.execute("""WITH neigh AS (
                SELECT a AS node, b AS other FROM _edges UNION SELECT b, a FROM _edges),
            propose AS (
                SELECT n.node, least(n.root, min(m.root)) AS r
                  FROM _nodes n JOIN neigh e ON e.node = n.node
                  JOIN _nodes m ON m.node = e.other
                 GROUP BY n.node, n.root)
            UPDATE _nodes AS t SET root = p.r
            FROM propose p
            WHERE p.node = t.node AND p.r < t.root
            RETURNING 1""").fetchall()
        if not changed:
            break
    # pick canonical cluster_id = min live id (fall back to min of all if the cluster is all-deleted)
    con.execute("""CREATE OR REPLACE TEMP TABLE crm_clusters AS
        WITH roots AS (SELECT root, min(node) FILTER (WHERE NOT deleted) AS live_min,
                              min(node) AS any_min FROM _nodes GROUP BY root)
        SELECT n.node AS crm_customer_id,
               coalesce(r.live_min, r.any_min) AS cluster_id,
               n.deleted AS is_deleted
        FROM _nodes n JOIN roots r ON r.root = n.root""")
    big = con.execute("SELECT count(*) FROM (SELECT cluster_id FROM crm_clusters "
                      "GROUP BY cluster_id HAVING count(*) > 1)").fetchone()[0]
    log(f"  crm_clusters: {big:,} multi-member clusters ({time.time()-t0:.1f}s)")
    return big


# ------------------------------------------------------------------------------------- deterministic
def _ams_bridges(con, sample_n: int | None) -> list[dict]:
    """One row per (source_system, src_key, crm_customer_id) linked via account_monthly_snapshot."""
    con.execute(f"""CREATE OR REPLACE TEMP TABLE _ams_bridge AS
        SELECT product_type, account_id, min(crm_customer_id) AS crm_customer_id
          FROM main.account_monthly_snapshot
         WHERE crm_customer_id IN (SELECT crm_customer_id FROM silver.customers c WHERE {sample_filter('customers', 'c', n=sample_n)})
         GROUP BY product_type, account_id""")
    rows = []
    for product, source in AMS_PRODUCT_TO_SOURCE.items():
        n = con.execute(f"SELECT count(*) FROM _ams_bridge WHERE product_type = '{product}'").fetchone()[0]
        if n:
            rows.append({"product_type": product, "source_system": source, "n": n})
    return rows


def build_deterministic_links(con, sample_n: int | None, log=print) -> int:
    t0 = time.time()
    _ams_bridges(con, sample_n)
    con.execute(f"""CREATE OR REPLACE TEMP TABLE det_links AS
        -- 1. CRM itself (every CRM record is its own source key)
        SELECT 'crm' AS source_system, crm_customer_id AS source_key, crm_customer_id,
               'crm_identity' AS match_method
          FROM silver.customers WHERE {sample_filter('customers', n=sample_n)}
        UNION ALL
        -- 2. cards via ams
        SELECT 'cards', ca.card_account_id, b.crm_customer_id, 'bridge_ams'
          FROM silver.card_accounts ca JOIN _ams_bridge b ON b.account_id = ca.card_account_id
         WHERE b.product_type = 'card' AND {sample_filter('card_accounts', 'ca', n=sample_n)}
        UNION ALL
        -- 3. loans via ams
        SELECT 'loans', la.loan_id, b.crm_customer_id, 'bridge_ams'
          FROM silver.loan_accounts la JOIN _ams_bridge b ON b.account_id = la.loan_id
         WHERE b.product_type IN ('personal_loan','auto_loan','mortgage','unsecured_loc','student_loc')
           AND {sample_filter('loan_accounts', 'la', n=sample_n)}
        UNION ALL
        -- 4. deposits via ams
        SELECT 'deposits', da.deposit_account_id, b.crm_customer_id, 'bridge_ams'
          FROM silver.deposit_accounts da JOIN _ams_bridge b ON b.account_id = da.deposit_account_id
         WHERE b.product_type IN ('chequing','savings','tfsa_savings','usd_account')
           AND {sample_filter('deposit_accounts', 'da', n=sample_n)}
        UNION ALL
        -- 5. collections: coll_customer_ref is a CRM id copied at case open
        SELECT 'collections', cc.case_id, cc.coll_customer_ref, 'bridge_coll'
          FROM silver.collections_cases cc
         WHERE cc.coll_customer_ref IN (SELECT crm_customer_id FROM silver.customers c WHERE {sample_filter('customers', 'c', n=sample_n)})
        UNION ALL
        -- 6. external bureau: bank_subject_ref -> padded CIF -> deposits -> ams -> crm
        SELECT 'external', e.bureau_request_id, b.crm_customer_id, 'bridge_cif'
          FROM silver.external e
          JOIN silver.deposit_accounts d ON d.src_customer_ref = e.bank_subject_ref
          JOIN _ams_bridge b ON b.account_id = d.deposit_account_id
         WHERE b.product_type IN ('chequing','savings','tfsa_savings','usd_account')
           AND {sample_filter('customers', n=sample_n) if sample_n else 'TRUE'}""")
    n = con.execute("SELECT count(*) FROM det_links").fetchone()[0]
    log(f"  deterministic links: {n:,} ({time.time()-t0:.1f}s)")
    return n


# ---------------------------------------------------------------- Splink (with rule-based fallback)
SPLINK_SETTINGS_PATH = Path("models/splink_settings.json")


def _splink_dedupe(con, train_n: int, log=print) -> list[dict] | None:
    """Train Splink on a train_n-row sample of silver.customers; score the whole sample.
    Returns [{crm_a, crm_b, probability}] for pairs with probability >= STEWARD_LOW.
    Returns None on failure (OOM, exception, no pairs)."""
    try:
        from splink import Linker, SettingsCreator, DuckDBAPI, block_on
        from splink import comparison_library as cl
    except ImportError as e:
        log(f"  splink import failed ({e}); using rule-based scorer")
        return None
    try:
        # project only columns Splink needs; this keeps memory small on 1M customers
        df_in = con.execute("""SELECT crm_customer_id AS unique_id, first_name, last_name,
                   dob_parsed AS dob, primary_phone_e164 AS phone,
                   substr(primary_phone_e164, 3, 10) AS phone10,
                   fsa, email, cast(year(dob_parsed) AS VARCHAR) AS birth_year
            FROM silver.customers
            WHERE crm_customer_id IN (SELECT crm_customer_id FROM crm_clusters)""").df()
        if len(df_in) < 100:
            log(f"  splink: {len(df_in)} input rows too few; using rule-based scorer")
            return None
        settings = SettingsCreator(
            link_type="dedupe_only",
            blocking_rules_to_generate_predictions=[
                block_on("fsa", "birth_year"),
                block_on("phone10"),
            ],
            comparisons=[
                cl.NameComparison("first_name"),
                cl.NameComparison("last_name"),
                cl.DateOfBirthComparison("dob", input_is_string=False),
                cl.ExactMatch("phone10").configure(term_frequency_adjustments=True),
                cl.ExactMatch("fsa"),
                cl.EmailComparison("email"),
            ],
            retain_matching_columns=False,
            retain_intermediate_calculation_columns=False,
        )
        db_api = DuckDBAPI()
        sdf = db_api.register(df_in, table_name="customers_in")
        linker = Linker(sdf, settings)
        # EM training on each blocking rule; this is the slow part
        linker.training.estimate_u_using_random_sampling(max_pairs=min(train_n * 50, 2_000_000))
        for rule in [block_on("fsa", "birth_year"), block_on("phone10")]:
            try:
                linker.training.estimate_parameters_using_expectation_maximisation(rule)
            except Exception as e:    # one rule can starve on sparse data; continue with the other
                log(f"  splink EM on {rule} failed ({str(e)[:80]}); continuing")
        SPLINK_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        linker.misc.save_model_to_json(str(SPLINK_SETTINGS_PATH), overwrite=True)
        preds = linker.inference.predict(threshold_match_probability=STEWARD_LOW)
        df = preds.as_pandas_dataframe()
        return [{"crm_a": r["unique_id_l"], "crm_b": r["unique_id_r"],
                 "match_probability": float(r["match_probability"])} for _, r in df.iterrows()]
    except Exception as e:
        log(f"  splink dedupe failed ({str(e)[:120]}); using rule-based scorer")
        return None


def _rule_dedupe(con, log=print) -> list[dict]:
    """Fallback scorer with the same thresholds. Score 1.0 for an exact match on name+dob,
    0.90 for name+dob with one component via dob_alt, 0.80 for name+phone10, 0.72 for name+fsa+email."""
    log("  rule scorer: comparing on name+dob / name+phone / name+fsa+email")
    rows = con.execute("""
        WITH c AS (SELECT crm_customer_id, lower(first_name) fn, lower(last_name) ln,
                           dob_parsed dob, dob_alt da,
                           substr(primary_phone_e164, 3, 10) p10, fsa, lower(email) em
                   FROM silver.customers
                   WHERE crm_customer_id IN (SELECT crm_customer_id FROM crm_clusters))
        SELECT a.crm_customer_id crm_a, b.crm_customer_id crm_b,
               greatest(
                 CASE WHEN a.fn = b.fn AND a.ln = b.ln AND a.dob IS NOT NULL AND a.dob = b.dob THEN 1.0
                      WHEN a.fn = b.fn AND a.ln = b.ln AND a.dob IS NOT NULL AND (a.dob = b.da OR a.da = b.dob) THEN 0.9
                      ELSE 0 END,
                 CASE WHEN a.fn = b.fn AND a.ln = b.ln AND a.p10 IS NOT NULL AND a.p10 = b.p10 THEN 0.8
                      ELSE 0 END,
                 CASE WHEN a.fn = b.fn AND a.ln = b.ln AND a.fsa = b.fsa AND a.em IS NOT NULL AND a.em = b.em THEN 0.72
                      ELSE 0 END) AS match_probability
          FROM c a JOIN c b
            ON a.crm_customer_id < b.crm_customer_id
           AND ((a.fsa = b.fsa AND year(a.dob) = year(b.dob))
                OR (a.p10 IS NOT NULL AND a.p10 = b.p10))
         WHERE a.fn = b.fn AND a.ln = b.ln""").fetchall()
    return [{"crm_a": r[0], "crm_b": r[1], "match_probability": r[2]} for r in rows if r[2] >= STEWARD_LOW]


def run_probabilistic(con, sample_n: int | None, log=print) -> list[dict]:
    """Try Splink; fall back to rule scorer. Pairs are added as extra edges to crm_clusters."""
    t0 = time.time()
    train_n = min(sample_n or 50_000, 50_000)
    pairs = _splink_dedupe(con, train_n, log) if train_n >= 2_000 else None
    if pairs is None:
        pairs = _rule_dedupe(con, log)
    method = "splink" if SPLINK_SETTINGS_PATH.exists() else "rules"
    _method_cached.set(method)
    log(f"  probabilistic: {len(pairs):,} candidate pairs (method={method}, {time.time()-t0:.1f}s)")
    # extend clusters with auto-merge pairs (>= 0.95)
    con.execute("CREATE OR REPLACE TEMP TABLE _prob_pairs AS SELECT NULL::VARCHAR crm_a, NULL::VARCHAR crm_b, NULL::DOUBLE p, NULL::VARCHAR band WHERE false")
    for p in pairs:
        band = "merge" if p["match_probability"] >= AUTO_MERGE else "steward"
        con.execute("INSERT INTO _prob_pairs VALUES (?, ?, ?, ?)",
                    [p["crm_a"], p["crm_b"], float(p["match_probability"]), band])
    # merge: union clusters of a and b
    # merge: for every auto-merge pair, both clusters adopt the lower cluster_id
    con.execute("""UPDATE crm_clusters AS cc SET cluster_id = sub.new_id
        FROM (SELECT c1.cluster_id AS old_id, least(c1.cluster_id, c2.cluster_id) AS new_id
                FROM _prob_pairs pp
                JOIN crm_clusters c1 ON c1.crm_customer_id = pp.crm_a
                JOIN crm_clusters c2 ON c2.crm_customer_id = pp.crm_b
               WHERE pp.band = 'merge' AND c1.cluster_id <> c2.cluster_id) sub
        WHERE cc.cluster_id = sub.old_id""")
    con.execute("CREATE OR REPLACE TABLE silver.steward_queue AS SELECT crm_a, crm_b, p AS match_probability FROM _prob_pairs WHERE band = 'steward'")
    return pairs


class _Marker:
    """Tiny module-level cache so the report writer can see the sample size and the method used
    without threading them through the whole call chain."""
    def __init__(self, default=None): self.v = default
    def set(self, v): self.v = v
    def get(self): return self.v
_method_cached = _Marker("rules")


# ------------------------------------------------------------------------------- id_xref assembly
def build_id_xref(con, pairs: list[dict], log=print) -> int:
    """Join every deterministic link to its CRM record's cluster to assign golden_id, and add CRM
    rows for every clustered customer. Writes silver.id_xref."""
    t0 = time.time()
    # cluster_id becomes golden_id; split evidence per method
    con.execute("""CREATE OR REPLACE TABLE silver.id_xref AS
        SELECT dl.source_system,
               dl.source_key,
               cc.cluster_id AS golden_id,
               dl.match_method,
               1.0 AS match_confidence,
               to_json({crm_customer_id: dl.crm_customer_id,
                        source_table: dl.match_method,
                        cluster_size: (SELECT count(*) FROM crm_clusters WHERE cluster_id = cc.cluster_id)}) AS evidence_json
          FROM det_links dl
          JOIN crm_clusters cc ON cc.crm_customer_id = dl.crm_customer_id""")
    # for Splink/rule probabilistic pairs that are in the steward band (not merged), log them as
    # "steward" evidence against the already-present CRM rows; nothing to add to id_xref
    n = con.execute("SELECT count(*) FROM silver.id_xref").fetchone()[0]
    log(f"  id_xref: {n:,} rows ({time.time()-t0:.1f}s)")
    return n


# ---------------------------------------------------------------------------------------- report
def write_match_report(con, pairs: list[dict], out: str = "reports/match_report.md") -> str:
    """Precision/recall vs the deterministic truth (CRM pointer + national_id_hash) + coverage/method mix."""
    from tabulate import tabulate
    # ground truth: ordered pairs (least, greatest) so (a, b) and (b, a) count once
    con.execute("""CREATE OR REPLACE TEMP TABLE _truth AS
        SELECT DISTINCT least(ca, cb) AS crm_a, greatest(ca, cb) AS crm_b FROM (
            SELECT a.crm_customer_id ca, b.crm_customer_id cb FROM silver.customers a JOIN silver.customers b
             ON a.national_id_hash = b.national_id_hash AND a.crm_customer_id < b.crm_customer_id
             WHERE a.national_id_hash IS NOT NULL
               AND a.crm_customer_id IN (SELECT crm_customer_id FROM crm_clusters)
               AND b.crm_customer_id IN (SELECT crm_customer_id FROM crm_clusters)
            UNION
            SELECT c.crm_customer_id, c.duplicate_of_crm_id FROM silver.customers c
             WHERE c.duplicate_of_crm_id IS NOT NULL
               AND c.crm_customer_id IN (SELECT crm_customer_id FROM crm_clusters)
               AND c.duplicate_of_crm_id IN (SELECT crm_customer_id FROM crm_clusters))""")
    truth_n = con.execute("SELECT count(*) FROM _truth").fetchone()[0]
    con.execute("""CREATE OR REPLACE TEMP TABLE _preds AS
        SELECT DISTINCT least(crm_a, crm_b) AS crm_a, greatest(crm_a, crm_b) AS crm_b, max(p) AS p
        FROM _prob_pairs GROUP BY least(crm_a, crm_b), greatest(crm_a, crm_b)""")
    tp = con.execute("SELECT count(*) FROM _truth t JOIN _preds p USING (crm_a, crm_b)").fetchone()[0]
    preds_n = con.execute("SELECT count(*) FROM _preds").fetchone()[0]
    recall = tp / max(truth_n, 1)
    precision = tp / max(preds_n, 1)
    coverage = con.execute("""SELECT source_system, count(DISTINCT source_key) AS keys_linked,
                                     count(DISTINCT CASE WHEN match_method LIKE 'bridge%' OR match_method='crm_identity' THEN source_key END) AS deterministic
                              FROM silver.id_xref GROUP BY source_system ORDER BY source_system""").fetchall()
    # count the source keys THAT WERE IN SCOPE for this run (sample-restricted when sampling), so the
    # coverage % is honest (comparing linked keys to the universe we actually processed)
    N = _sample_n_cached.get()
    source_totals = {src: con.execute(f"SELECT count(DISTINCT {col}) FROM silver.{tbl} WHERE "
                                      + sample_filter(tbl, n=N)).fetchone()[0]
                     for src, tbl, col in [
                         ("cards", "card_accounts", "card_account_id"),
                         ("loans", "loan_accounts", "loan_id"),
                         ("deposits", "deposit_accounts", "deposit_account_id"),
                         ("collections", "collections_cases", "case_id"),
                         ("external", "external", "bureau_request_id"),
                         ("crm", "customers", "crm_customer_id")]}
    rows, flagged = [], []
    for src, keys_linked, det in coverage:
        total = source_totals.get(src, keys_linked)
        pct = 100 * keys_linked / max(total, 1)
        det_pct = 100 * det / max(total, 1)
        rows.append((src, f"{keys_linked:,}/{total:,}", f"{pct:.1f}%", f"{det_pct:.1f}%"))
        if det_pct < 90 and src != "crm":
            flagged.append(f"**{src}**: deterministic coverage {det_pct:.1f}% - fix the bridge, do not paper over with Splink")
    examples = {}
    for band_lo, band_hi, label in [(AUTO_MERGE, 1.01, "merge (>=0.95)"), (STEWARD_LOW, AUTO_MERGE, "steward (0.70-0.95)")]:
        examples[label] = con.execute(
            f"SELECT crm_a, crm_b, round(p,3) FROM _prob_pairs WHERE p >= {band_lo} AND p < {band_hi} ORDER BY p DESC LIMIT 5"
        ).fetchall()
    md = [
        f"# Identity resolution report",
        f"Snapshot: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Sample: N={_sample_n_cached.get() or 'full'}" + (" (silver.* sample)" if _sample_n_cached.get() else " customers"),
        f"Probabilistic method: **{_method_cached.get()}** (splink falls back to rules if training fails)",
        "",
        "## Probabilistic matcher vs deterministic truth (CRM pointer + national_id_hash)",
        f"- Truth pairs: {truth_n:,}",
        f"- Predicted (any band): {preds_n:,}",
        f"- True positives: {tp:,}",
        f"- **Recall**: {recall:.3f} (of known CRM duplicates found)",
        f"- **Precision**: {precision:.3f} (floor only: non-truth predictions include real duplicates "
        f"the CRM did not record, so true precision is higher - needs manual spot-checks)",
        "",
        "## Coverage by source",
        tabulate(rows, headers=["source", "keys linked / total", "coverage %", "deterministic %"], tablefmt="github"),
        "",
    ]
    if flagged:
        md += ["### Bridge-coverage warnings", ""] + ["- " + f for f in flagged] + [""]
    md += ["## Example pairs per band", ""]
    for label, ex in examples.items():
        md += [f"### {label}", "", tabulate(ex, headers=["crm_a", "crm_b", "probability"], tablefmt="github"), ""]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(md), encoding="utf-8")
    return out


_sample_n_cached = _Marker()


# ---------------------------------------------------------------------------------- orchestrator
def run_match(cfg: dict, sample_n: int | None = None, log=print) -> dict:
    con = duckdb.connect(cfg["db_path"])
    scfg = cfg.get("silver", {})
    con.execute(f"SET memory_limit='{scfg.get('memory_limit', '4GB')}'; SET threads={int(scfg.get('threads', 4))}; "
                "SET preserve_insertion_order=false;")
    _sample_n_cached.set(sample_n)
    if sample_n:
        build_sample(con, sample_n, log=log)
    build_crm_clusters(con, sample_n, log)
    build_deterministic_links(con, sample_n, log)
    pairs = run_probabilistic(con, sample_n, log)
    build_id_xref(con, pairs, log)
    out = write_match_report(con, pairs)
    log(f"  match report -> {out}")
    con.close()
    return {"id_xref": out, "pairs": len(pairs)}
