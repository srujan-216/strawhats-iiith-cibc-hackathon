"""One test per CLAUDE.md section 5 rule, plus 'hardship never harsher' invariant."""
import pandas as pd
from src.layer4.policy_gate import allowed_actions, allowed_actions_vectorised, ALL


def _case(**k):
    base = {"insolvency_hold_flag": False, "deceased_hold_flag": False, "cease_contact_flag": False,
            "dispute_flag": False, "third_party_rep_flag": False, "vulnerable_customer_flag": False,
            "hardship_flag": False, "current_bucket": "current", "primary_product": "card"}
    base.update(k)
    return pd.Series(base)


def _feats(**k):
    base = {"contacts_last_7d": 0, "vulnerability_signal": False, "txt_hardship_signal": "none"}
    base.update(k)
    return pd.Series(base)


def test_insolvency_hold_only_no_contact():
    a = allowed_actions(_case(insolvency_hold_flag=True), _feats())
    assert a["no_contact"] and not any(a[x] for x in ALL if x != "no_contact")
    assert "insolvency" in a._reasons["call_best_time"][1]


def test_deceased_hold_only_no_contact():
    a = allowed_actions(_case(deceased_hold_flag=True), _feats())
    assert a["no_contact"] and not any(a[x] for x in ALL if x != "no_contact")


def test_cease_contact_blocks_outbound():
    a = allowed_actions(_case(cease_contact_flag=True), _feats())
    assert a["no_contact"] and not a["digital_nudge"] and not a["call_best_time"]
    assert not a["payment_plan"] and not a["escalate"]


def test_open_dispute_blocks_pressure_actions():
    a = allowed_actions(_case(dispute_flag=True), _feats())
    assert not a["call_best_time"] and not a["escalate"] and not a["digital_nudge"]


def test_third_party_rep_routes_to_representative():
    a = allowed_actions(_case(third_party_rep_flag=True), _feats())
    assert a["hardship_referral"]
    assert not a["digital_nudge"] and not a["call_best_time"] and not a["escalate"]


def test_contact_cap_blocks_call_at_3_and_digital_at_5():
    a = allowed_actions(_case(), _feats(contacts_last_7d=3))
    assert not a["call_best_time"] and a["digital_nudge"]
    a = allowed_actions(_case(), _feats(contacts_last_7d=5))
    assert not a["call_best_time"] and not a["digital_nudge"]


def test_hardship_blocks_escalate_never_harsher():
    """Core invariant: a hardship flag must NEVER route to escalate / legal_handoff."""
    for extra in [{}, {"vulnerable_customer_flag": True}, {"dispute_flag": True}]:
        a = allowed_actions(_case(hardship_flag=True, **extra), _feats())
        assert not a["escalate"], f"hardship escalated with extras={extra}"
    # also via text-only hardship signal from the classifier
    a = allowed_actions(_case(), _feats(txt_hardship_signal="clear"))
    assert not a["escalate"]
    # and via vulnerability_signal
    a = allowed_actions(_case(), _feats(vulnerability_signal=True))
    assert not a["escalate"]


def test_vulnerable_customer_blocks_escalate():
    a = allowed_actions(_case(vulnerable_customer_flag=True), _feats())
    assert not a["escalate"]


def test_90plus_without_hardship_blocks_digital_and_call():
    a = allowed_actions(_case(current_bucket="121-150"), _feats())
    assert not a["digital_nudge"] and not a["call_best_time"]
    assert a["escalate"] and a["payment_plan"]
    # but hardship 90+ gets supportive treatment
    a = allowed_actions(_case(current_bucket="121-150", hardship_flag=True), _feats())
    assert a["hardship_referral"] and not a["escalate"]


def test_normal_case_everything_allowed():
    a = allowed_actions(_case(), _feats())
    assert all(a[x] for x in ALL)


def test_vectorised_matches_row_version():
    """Spot-check: vectorised allowed_actions_vectorised matches the per-row version on a mixed batch."""
    df = pd.DataFrame([
        _case().to_dict(),
        _case(insolvency_hold_flag=True).to_dict(),
        _case(cease_contact_flag=True).to_dict(),
        _case(hardship_flag=True).to_dict(),
        _case(current_bucket="151-180").to_dict(),
    ])
    # add feature cols
    df["contacts_last_7d"] = [0, 0, 0, 4, 0]
    df["vulnerability_signal"] = False
    df["txt_hardship_signal"] = "none"
    v = allowed_actions_vectorised(df)
    for i in range(len(df)):
        per_row = allowed_actions(df.iloc[i], df.iloc[i])
        for a in ALL:
            assert bool(v[a].iloc[i]) == per_row[a], f"row {i} action {a}"
