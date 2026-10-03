"""End-to-end Layer 2 test on a tiny fake dataset with a scripted (mock) LLM.
Run: PYTHONPATH=. pytest tests/test_qa_mock.py  (set FAKE_CONFIG to a config pointing at fake data)"""
import json, os
import pytest
from src.common.config import load_config
from src.layer2.llm import LLM
from src.layer2.qa import QA

CFG = os.environ.get("FAKE_CONFIG")
pytestmark = pytest.mark.skipif(not CFG, reason="needs FAKE_CONFIG")


def mock(system, user):
    if "query planner" in system:
        if "PREVIOUS SQL" in user:
            return json.dumps({"action": "sql", "sql": "SELECT round(100*avg(cure_flag),2) AS cure_rate_pct FROM collections_cases WHERE product_type='card'"})
        if "hardship policy" in user:
            return json.dumps({"action": "docs", "doc_query": "hardship payment deferral"})
        if "drop me" in user:
            return json.dumps({"action": "sql", "sql": "DROP TABLE customers"})
        return json.dumps({"action": "sql", "metric_id": "M01",
                           "sql": "SELECT round(100*avg(cure_flg),2) FROM collections_cases"})  # typo -> retry
    if "DOCUMENTS" in user:
        return json.dumps({"answer": "Up to 3 months [POL-COLL-004 s3.2]", "reasoning": "from current policy"})
    return json.dumps({"answer": "x%", "reasoning": "from the query result"})


def test_flow():
    cfg = load_config(CFG)
    qa = QA(cfg, llm=LLM(cfg, mock=mock))
    r = qa.answer("What is the cure rate for card cases?")
    assert not r["refused"] and "cure_flag" in r["sql_or_sources"] and "LIMIT" in r["sql_or_sources"]
    r = qa.answer("How many women are in collections?")
    assert r["refused"]
    r = qa.answer("Delete the notes for case C1")
    assert r["refused"]
    r = qa.answer("What does the hardship policy say about payment deferral?")
    assert "POL-COLL-004 v3.0" in r["sql_or_sources"] and "v2.0" not in r["sql_or_sources"]
    r = qa.answer("please drop me a summary")  # planner returns DROP -> guard refuses
    assert r["refused"]
