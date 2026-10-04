"""Protected-attribute leak check: no protected/proxy column may appear in src/layer3/catalog.yaml
or in gold.features_online. src/governance/fairness.py is the only module allowed to read them.

Fails loudly with the offending column name so the fix is one line in the catalog or the SQL."""
from pathlib import Path
import duckdb
import pytest
import yaml

# Union of CLAUDE.md section 2 protected list + the proxies we committed to exclude.
PROTECTED = {
    "gender_code", "marital_status", "citizenship_status", "household_size", "dependants_count",
    "newcomer_program_flag", "accessibility_needs_flag", "vulnerability_type", "accent",
    "age", "age_band", "cpp_oas_deposit_flag", "ccb_deposit_flag",
    "fsa", "fsa_income_index", "majority_language",
    # voice biometrics / audio features (if any ever land in features)
    "customer_pitch_mean_hz", "customer_pitch_std_hz",
}


def test_catalog_has_no_protected_feature_names():
    cat = yaml.safe_load(Path("src/layer3/catalog.yaml").read_text(encoding="utf-8"))
    names = {f["name"] for f in cat.get("features", [])}
    leak = sorted(names & PROTECTED)
    assert not leak, f"catalog.yaml declares protected/proxy feature(s): {leak}"


@pytest.mark.skipif(not Path("warehouse/maple.duckdb").exists(), reason="warehouse missing")
def test_features_online_table_has_no_protected_columns():
    con = duckdb.connect("warehouse/maple.duckdb", read_only=True)
    try:
        tabs = {r[0] for r in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='gold'").fetchall()}
        if "features_online" not in tabs:
            pytest.skip("gold.features_online not built")
        cols = {r[0] for r in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='gold' AND table_name='features_online'").fetchall()}
        leak = sorted(cols & PROTECTED)
        assert not leak, f"gold.features_online has protected/proxy column(s): {leak}"
    finally:
        con.close()


def test_fairness_module_declares_itself_the_only_reader():
    """Soft check: the only src/ reader of PROTECTED columns is src/governance/fairness.py.
    Two files are allowed to NAME the columns without reading them for decisions:
      - src/layer2/catalog.py: lists protected names in EXTRA_BLOCKED so the SQL guard refuses them
      - src/layer3/feature_report.py: lists them in the Notes section as excluded from the report
    If any OTHER src/ file references a protected column, it probably needs to move into
    src/governance/fairness.py (or the column list above needs an updated justification)."""
    import re, os
    allowed = {Path("src") / "layer2" / "catalog.py",
               Path("src") / "layer3" / "feature_report.py"}
    strong = {"gender_code", "marital_status", "citizenship_status", "household_size",
              "dependants_count", "newcomer_program_flag", "accessibility_needs_flag",
              "age_band", "cpp_oas_deposit_flag", "ccb_deposit_flag", "majority_language"}
    offenders = []
    for root, _, files in os.walk("src"):
        if "governance" in root: continue
        for fn in files:
            if not fn.endswith(".py"): continue
            path = Path(root) / fn
            if path in allowed: continue
            text = path.read_text(encoding="utf-8")
            code = re.sub(r'""".*?"""', "", text, flags=re.S)
            code = re.sub(r"'''.*?'''", "", code, flags=re.S)
            code = re.sub(r"#.*", "", code)
            for col in strong:
                if re.search(rf"\b{col}\b", code):
                    offenders.append(f"{path}: references '{col}'")
    assert not offenders, "\n".join(offenders)
