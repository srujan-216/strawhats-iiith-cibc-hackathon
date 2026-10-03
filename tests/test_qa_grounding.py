"""Grounding guardrails: never ship a confident wrong answer.

Rules:
  - SELECT that returns 0 rows -> answer is "I don't have data for that", SQL shown, no LLM guess.
  - Doc query with 0 chunks -> refuse "no current policy covers this".
  - SQL fix loop exhausted  -> refuse with the last error summarised.
  - Every non-refusal answer must carry sql_or_sources + reasoning + badge; if any is empty,
    the answer is downgraded to a refusal."""
import json
import duckdb
import pytest
from src.layer2.llm import LLM
from src.layer2.qa import QA


def _cfg(tmp_path):
    db = tmp_path / "t.duckdb"
    audit = tmp_path / "a.jsonl"
    con = duckdb.connect(str(db))
    # minimal main.* tables so Catalog loads; "customers" is enough to be an allowed table
    con.execute("CREATE SCHEMA IF NOT EXISTS main; CREATE TABLE main.customers (crm_customer_id VARCHAR); "
                "CREATE TABLE main.collections_cases (case_id VARCHAR, case_status VARCHAR); "
                "CREATE TABLE main.metric_definitions (metric_id VARCHAR, metric_name VARCHAR, "
                "business_definition VARCHAR, formula VARCHAR, grain VARCHAR, time_basis VARCHAR, "
                "default_filters VARCHAR, unit VARCHAR, synonyms VARCHAR, source_tables VARCHAR, "
                "certified_flag BOOLEAN)")
    con.close()
    return {"db_path": str(db), "audit_log": str(audit), "data_dir": str(tmp_path),
            "guard": {"row_limit": 1000, "timeout_s": 5, "max_retries": 2},
            "llm": {"cache_path": str(tmp_path / "c.sqlite"), "providers": [], "routes": {"default": []}}}


def _qa(tmp_path, mock):
    cfg = _cfg(tmp_path)
    return QA(cfg, llm=LLM(cfg, mock=mock))


def test_zero_rows_never_invents_a_number(tmp_path):
    """SELECT returns 0 rows -> fixed message, SQL shown, LLM never called for the answer."""
    answer_calls = []
    def mock(system, user):
        if "query planner" in system:
            return json.dumps({"action": "sql", "sql": "SELECT crm_customer_id FROM customers WHERE 1=0"})
        answer_calls.append(user)
        return json.dumps({"answer": "42 cases", "reasoning": "hallucinated"})
    r = _qa(tmp_path, mock).answer("How many open collections cases are there?")
    assert r["answer"] == "I don't have data for that."
    assert "SELECT crm_customer_id" in r["sql_or_sources"]
    assert not r["refused"]                 # it is a safe empty answer, not a refusal
    assert r["badge"] == "exploratory"
    assert answer_calls == []               # the ANSWER_SYSTEM prompt is never sent


def test_sql_retry_exhausted_refuses_with_error(tmp_path):
    """Every planner call returns broken SQL; after guard.max_retries, refuse with the error."""
    def mock(system, user):
        return json.dumps({"action": "sql", "sql": "SELECT bogus_col FROM customers"})
    cfg = _cfg(tmp_path)
    qa = QA(cfg, llm=LLM(cfg, mock=mock))
    r = qa.answer("Count the cases")
    assert r["refused"] and r["badge"] == "refused"
    assert "could not produce a valid query" in r["answer"]
    assert "bogus_col" in r["answer"]       # the error summary mentions the broken column
    assert "bogus_col" in r["sql_or_sources"]


def test_zero_doc_chunks_refuses_with_fixed_wording(tmp_path, monkeypatch):
    def mock(system, user):
        return json.dumps({"action": "docs", "doc_query": "nonexistent policy about mars"})
    cfg = _cfg(tmp_path)
    qa = QA(cfg, llm=LLM(cfg, mock=mock))
    class EmptyIndex:
        def search(self, q, k=5): return []
    monkeypatch.setattr(QA, "docs", property(lambda self: EmptyIndex()))
    r = qa.answer("Is there a policy about Mars collections?")
    assert r["refused"] and r["badge"] == "refused"
    assert r["answer"].endswith("no current policy covers this")


def test_non_refusal_answer_always_has_sql_reasoning_badge(tmp_path):
    """If the answer LLM returns empty reasoning, grounding downgrades the answer to a refusal."""
    def mock(system, user):
        if "query planner" in system:
            return json.dumps({"action": "sql", "metric_id": "M01",
                               "sql": "SELECT count(*) AS n FROM customers"})
        return json.dumps({"answer": "There are 0 cases", "reasoning": ""})     # empty reasoning
    cfg = _cfg(tmp_path)
    duckdb.connect(cfg["db_path"]).execute("INSERT INTO main.customers VALUES ('A-1')").close()
    r = QA(cfg, llm=LLM(cfg, mock=mock)).answer("How many customers?")
    assert r["refused"]                     # downgraded, not shipped
    assert "missing required grounding (reasoning)" in r["answer"]
    assert r["badge"] == "refused"


def test_refused_answer_also_has_badge(tmp_path):
    r = _qa(tmp_path, lambda s, u: json.dumps({"action": "refuse", "reason": "out of scope"})).answer("x")
    assert r["refused"] and r["badge"] == "refused"


@pytest.mark.parametrize("metric_id,want", [("M01", "certified"), (None, "exploratory")])
def test_certified_vs_exploratory_badge(tmp_path, metric_id, want):
    """metric_id present -> certified; absent -> exploratory."""
    def mock(system, user):
        if "query planner" in system:
            return json.dumps({"action": "sql", "metric_id": metric_id,
                               "sql": "SELECT count(*) AS n FROM customers"})
        return json.dumps({"answer": "1", "reasoning": "one row"})
    cfg = _cfg(tmp_path)
    duckdb.connect(cfg["db_path"]).execute("INSERT INTO main.customers VALUES ('A-1')").close()
    r = QA(cfg, llm=LLM(cfg, mock=mock)).answer("How many customers?")
    assert not r["refused"] and r["badge"] == want
