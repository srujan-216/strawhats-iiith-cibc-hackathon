"""Layer 2: plain-English question -> answer with the SQL or sources shown.

Flow: rule scope check -> LLM plan (sql | text_sql | docs | refuse) -> SQL guard ->
execute (read-only, timeout) -> retry on error -> LLM writes the answer from the result only.
Every step is written to the audit log."""
from __future__ import annotations
import json, re
import duckdb
from src.common.audit import AuditLog
from src.layer2.catalog import Catalog
from src.layer2.guard import GuardError, execute_guarded, validate
from src.layer2.llm import LLM
from src.layer2.rag_docs import DocIndex


JSON_RETRY_SUFFIX = ("\n\nReturn VALID JSON. The previous response was truncated or malformed.")

DEFAULT_AS_OF = "2026-09-28"

_WRITE = re.compile(r"^\s*(please\s+|can you\s+|could you\s+|go ahead and\s+|i want you to\s+)?"
                    r"(delete|drop|truncate|update|insert|alter|overwrite|remove|change|set|move|send|waive|write[- ]?off|"
                    r"close|cancel|mark|assign|email|text|call)\b|\b(drop|truncate|delete from|insert into|alter)\s+table\b", re.I)
_PROTECTED = re.compile(r"\b(gender|sex|women|men|female|male|marital|married|single mothers?|divorced|citizenship|"
                        r"citizens?|immigrants?|newcomers?|household size|dependants?|children|accent|disabilit\w*|"
                        r"accessibility|religio\w*|race|ethnic\w*|pregnan\w*)\b", re.I)

PLAN_SYSTEM = """You are the query planner for Maple Bank's collections analytics assistant.
Users are collections managers and agents. Data is in DuckDB; today's date for the question is given as AS_OF.

Decide ONE action:
- "sql": the answer comes from structured data. Write one DuckDB SELECT.
- "text_sql": the answer needs agent notes or call transcripts for a customer/case. Write one SELECT that returns
  the id column(s) and the text column(s) of the relevant notes/turns (most recent first, max 30 rows).
- "docs": the answer is in bank policy/procedure documents. Give a short search query in "doc_query".
- "refuse": the question asks for protected attributes (gender, marital status, citizenship, household, newcomer,
  accessibility, vulnerability type, accent, age-based treatment), wants to change/delete/send anything,
  asks for data outside collections, personal opinions, or anything the tables cannot answer.

SQL rules:
- Only use the tables and columns listed. Never use protected attributes.
- If a CERTIFIED METRIC matches the question, follow its formula, grain, time_basis and default_filters exactly.
- Relative dates ("last 90 days", "this month") are relative to AS_OF, not to today's clock.
- Columns stored as text may need TRY_CAST / TRY_STRPTIME. Dates may come in mixed formats.
- Return tidy, labelled columns. Round percentages to 2 decimals. No LIMIT needed for aggregates.

Return JSON: {"action": "...", "reason": "<one sentence>", "metric_id": "<id or null>",
              "sql": "<query or null>", "doc_query": "<text or null>"}"""

ANSWER_SYSTEM = """You write the final answer for a collections analytics assistant.
Use ONLY the result rows / documents provided. Never invent numbers.
Start with the direct answer (the number with its unit, or the short fact), then at most one sentence of context.
Percentages: 2 decimals with %. Money: CAD with 2 decimals. Counts: integers.
For notes, transcripts or documents, cite ids in square brackets, e.g. [N-48213] or [POL-COLL-004 s3.2].
Return JSON: {"answer": "<answer text>", "reasoning": "<one line: how the answer follows from the data>"}"""


class QA:
    def __init__(self, cfg: dict, llm: LLM | None = None, role: str = "manager"):
        self.cfg = cfg
        self.audit = AuditLog(cfg["audit_log"])
        self.llm = llm or LLM(cfg, self.audit)
        self.con = duckdb.connect(cfg["db_path"], read_only=True)
        self.cat = Catalog(self.con, cfg["data_dir"])
        self.role = role
        self._docs = None

    @property
    def docs(self) -> DocIndex:
        if self._docs is None:
            self._docs = DocIndex(self.con, self.cfg["data_dir"],
                                  self.cfg["db_path"].replace(".duckdb", "_docs.pkl"))
        return self._docs

    # ------------------------------------------------------------------
    def answer(self, question: str, as_of: str | None = None) -> dict:
        as_of = as_of or DEFAULT_AS_OF
        res = {"question": question, "answer": "", "sql_or_sources": "", "refused": False,
               "reasoning": "", "badge": ""}
        rule = self._rule_scope(question)
        if rule:
            return self._refuse(res, rule, "rule")

        metrics = self.cat.metric_matches(question)
        tables = self.cat.relevant_tables(question, metrics)
        user = (f"AS_OF: {as_of}\nQUESTION: {question}\n\nCERTIFIED METRICS:\n{self.cat.metrics_block(metrics)}\n\n"
                f"TABLES:\n{self.cat.schema_block(tables, question)}")
        plan = self.llm.complete_json(PLAN_SYSTEM, user, purpose="plan")
        action = (plan.get("action") or "").lower()
        self.audit.write("plan", question=question, action=action, metric_id=plan.get("metric_id"), tables=tables)

        # certified = planner matched one of our metric_definitions; exploratory otherwise
        res["badge"] = "certified" if plan.get("metric_id") else "exploratory"
        if action == "refuse":
            return self._refuse(res, plan.get("reason", "out of scope"), "llm")
        if action == "docs":
            return self._check_grounding(self._answer_docs(res, question, plan.get("doc_query") or question))
        if action in ("sql", "text_sql"):
            return self._check_grounding(self._answer_sql(res, question, user, plan, action))
        return self._refuse(res, "could not map the question to the available data", "planner")

    def _check_grounding(self, res: dict) -> dict:
        """Non-refusal answers must carry SQL or at least one citation, a reasoning line, and a badge.
        If any is empty the answer is downgraded to a refusal: never ship a confident wrong answer."""
        if res["refused"]:
            return res
        missing = [k for k in ("sql_or_sources", "reasoning", "badge") if not str(res.get(k, "")).strip()]
        if missing:
            return self._refuse(res, f"answer missing required grounding ({', '.join(missing)})", "grounding")
        return res

    # ------------------------------------------------------------------
    def _rule_scope(self, q: str) -> str | None:
        if _WRITE.search(q):
            return "The assistant is read-only: it cannot change, delete or send anything. It can raise a recommendation for a person instead."
        m = _PROTECTED.search(q)
        if m:
            return f"The question uses a protected attribute ({m.group(0)}), which cannot be used for analysis or decisions."
        return None

    def _refuse(self, res: dict, reason: str, by: str) -> dict:
        res.update(answer=f"I can't answer this. {reason}", refused=True, reasoning=f"refused by {by}",
                   badge="refused")
        self.audit.write("refusal", question=res["question"], reason=reason, by=by)
        return res

    def _answer_sql(self, res, question, user, plan, action) -> dict:
        allowed = set(self.cat.tables)
        sql_in, last_err = plan.get("sql") or "", ""
        for attempt in range(self.cfg["guard"]["max_retries"] + 1):
            try:
                sql = validate(sql_in, allowed, self.cfg["guard"]["row_limit"], self.cat.protected)
                df = execute_guarded(self.con, sql, self.cfg["guard"]["timeout_s"])
                break
            except GuardError as e:
                last_err = f"guard: {e}"
                if "protected attribute" in str(e) or "forbidden" in str(e):
                    return self._refuse(res, str(e), "guard")
            except duckdb.Error as e:
                last_err = f"duckdb: {str(e)[:400]}"
            self.audit.write("sql_error", question=question, sql=sql_in, error=last_err, attempt=attempt)
            fix = self.llm.complete_json(PLAN_SYSTEM, f"{user}\n\nYOUR PREVIOUS SQL:\n{sql_in}\nERROR:\n{last_err}\n"
                                         "Return corrected JSON.", purpose="sql_fix")
            sql_in = fix.get("sql") or sql_in
        else:
            # retries exhausted: refuse with the last error summary; sql shown so a human can fix it
            res["sql_or_sources"] = sql_in
            return self._refuse(res, f"could not produce a valid query (last error: {last_err[:200]})", "sql_retry")
        if len(df) == 0:
            # zero rows: never invent a number; show the SQL that returned nothing
            res.update(answer="I don't have data for that.", sql_or_sources=sql,
                       reasoning="query returned 0 rows")
            self.audit.write("answer_empty", question=question, sql=sql)
            return res
        rows = df.head(40).to_csv(index=False)
        answer_user = f"QUESTION: {question}\nSQL:\n{sql}\nRESULT ({len(df)} rows):\n{rows}"
        try:
            final = self.llm.complete_json(ANSWER_SYSTEM, answer_user, purpose="answer")
        except json.JSONDecodeError:
            # one retry with an explicit "return valid JSON" nudge before giving up
            self.audit.write("json_parse_retry", question=question, purpose="answer")
            try:
                final = self.llm.complete_json(ANSWER_SYSTEM, answer_user + JSON_RETRY_SUFFIX, purpose="answer")
            except json.JSONDecodeError as e:
                return self._refuse(res, f"the language model returned malformed JSON twice: {str(e)[:120]}",
                                    "json_parse")
        res.update(answer=final.get("answer", ""), sql_or_sources=sql, reasoning=final.get("reasoning", ""))
        self.audit.write("answer", question=question, sql=sql, rows=len(df), answer=res["answer"])
        return res

    def _answer_docs(self, res, question, query) -> dict:
        hits = self.docs.search(query, k=5)
        if not hits:
            return self._refuse(res, "no current policy covers this", "retrieval")
        ctx = "\n\n".join(f"[{h['doc_id']} v{h['version']} s:{h['section']}]\n{h['text'][:1500]}" for h in hits)
        docs_user = f"QUESTION: {question}\nDOCUMENTS:\n{ctx}"
        try:
            final = self.llm.complete_json(ANSWER_SYSTEM, docs_user, purpose="answer_docs")
        except json.JSONDecodeError:
            self.audit.write("json_parse_retry", question=question, purpose="answer_docs")
            try:
                final = self.llm.complete_json(ANSWER_SYSTEM, docs_user + JSON_RETRY_SUFFIX, purpose="answer_docs")
            except json.JSONDecodeError as e:
                return self._refuse(res, f"the language model returned malformed JSON twice: {str(e)[:120]}",
                                    "json_parse")
        sources = "; ".join(dict.fromkeys(f"{h['doc_id']} v{h['version']} ({h['section']})" for h in hits))
        res.update(answer=final.get("answer", ""), sql_or_sources=sources, reasoning=final.get("reasoning", ""))
        self.audit.write("answer", question=question, sources=sources, answer=res["answer"])
        return res
