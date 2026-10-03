from src.layer2.evaluate import _gold_table, _is_refusal, _tol, score_table

GOLD = "queue,avg_dpd,open_cases\nearly_stage,14.5,30922\nlate_stage,126.2,11017"


def test_gold_table_and_refusal_detection():
    assert _gold_table(GOLD)[0] == ["queue", "avg_dpd", "open_cases"]
    assert _gold_table("A maximum of 3 outbound call attempts.") is None
    assert _is_refusal("Refuse: protected ground") and not _is_refusal("No. The list applies")


def test_tolerances():
    assert _tol("±0.5 pts") == 0.5 and _tol("±0.1 days") == 0.1 and _tol("exact") == 0.5 and _tol(None) == 0.5


def test_score_table_within_tolerance():
    ours = "early_stage: 14.52 days, 30,922 cases; late_stage: 126.2 days, 11,017 cases"
    assert score_table(GOLD, ours, "±0.1 days")[0]
    assert not score_table(GOLD, ours.replace("14.52", "14.9"), "±0.1 days")[0]
    ok, detail = score_table(GOLD, "early_stage 14.5, 30922", "±0.1 days")
    assert not ok and "2/4" in detail
