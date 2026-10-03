"""Score our answers against the dev gold answers (dev split only; test is hidden).

Gold format (labels/benchmark_dev_answers.csv): gold_answer, gold_sql_reference, gold_sources, trap_notes.
- Refusal: gold_answer starts with "Refuse". Refusal accuracy = our `refused` flag equals the gold one.
- Table answers (header line + rows): every number in the gold's value columns (first column is the label
  when there are several) must appear somewhere in our answer within the question's tolerance
  ('±0.5 pts' -> 0.5, '±0.1 days' -> 0.1, 'exact' -> rounding only). Row labels are not matched.
- Text answers (documents, notes): not auto-scored, listed as "review" (counted separately).
Only this module reads gold answers, and only for dev scoring."""
from __future__ import annotations
import re
from pathlib import Path
import duckdb
import pandas as pd

_NUM = re.compile(r"-?\d[\d,]*\.?\d*")


def _numbers(text) -> list[float]:
    out = []
    for m in _NUM.findall(str(text)):
        try:
            out.append(float(m.replace(",", "")))
        except ValueError:
            pass
    return out


def _tol(t) -> float:
    """'±0.5 pts' -> 0.5; 'exact' or empty -> 0.5 (rounding only: counts are integers)."""
    t = str(t or "").lower().strip()
    if t in ("", "nan", "none", "exact"):
        return 0.5
    v = _numbers(t)
    return v[0] if v else 0.5


def _bool(x) -> bool:
    return str(x).strip().lower() in ("true", "1", "yes", "y")


def _is_refusal(gold: str) -> bool:
    return str(gold).strip().lower().startswith("refuse")


def _gold_table(gold: str):
    """(header, rows) when the gold answer is a CSV table, else None."""
    lines = [l for l in str(gold).strip().split("\n") if l.strip()]
    if len(lines) >= 2 and "," in lines[0] and re.fullmatch(r"[a-z0-9_,]+", lines[0].strip()):
        return lines[0].split(","), [l.split(",") for l in lines[1:]]
    return None


def score_table(gold: str, ours: str, tolerance) -> tuple[bool, str]:
    header, rows = _gold_table(gold)
    first_is_label = len(header) > 1
    want = []
    for r in rows:
        for cell in (r[1:] if first_is_label else r):
            v = _numbers(cell)
            if v:
                want.append(v[0])
    have, tol = _numbers(ours), _tol(tolerance)
    missing = [w for w in want if not any(abs(w - h) <= tol for h in have)]
    if missing:
        return False, f"{len(want) - len(missing)}/{len(want)} values (missing {missing[:3]})"
    return True, f"{len(want)}/{len(want)} values"


def evaluate(cfg, ours_csv: str, out_md: str) -> dict:
    con = duckdb.connect(cfg["db_path"], read_only=True)
    gold = con.execute("SELECT * FROM hidden.benchmark_dev_answers").df().astype(str)
    qs = con.execute("SELECT question_id, question_text, tolerance FROM main.benchmark_questions").df().astype(str)
    con.close()
    ours = pd.read_csv(ours_csv, dtype=str, keep_default_na=False)
    m = gold.merge(ours, on="question_id", how="left").merge(qs, on="question_id", how="left")
    rows, n_scored, n_ok, ref_ok = [], 0, 0, 0
    tp = fp = fn = 0
    for _, r in m.iterrows():
        g_ref, o_ref = _is_refusal(r["gold_answer"]), _bool(r.get("refused"))
        ans = r.get("answer")
        ans = "" if pd.isna(ans) else str(ans)
        ref_ok += g_ref == o_ref
        tp += g_ref and o_ref; fp += (not g_ref) and o_ref; fn += g_ref and not o_ref
        if g_ref or o_ref:
            verdict, kind = ("ok" if g_ref == o_ref else "refusal mismatch"), "refusal"
            n_scored += 1; n_ok += verdict == "ok"
        elif _gold_table(r["gold_answer"]):
            ok, detail = score_table(r["gold_answer"], ans, r.get("tolerance"))
            verdict, kind = ("ok" if ok else f"off: {detail}"), "table"
            n_scored += 1; n_ok += ok
        else:
            verdict, kind = "review", "text"
        rows.append((r["question_id"], kind, verdict, ans.replace("\n", " ")[:80], str(r["gold_answer"]).replace("\n", " | ")[:80]))
    df = pd.DataFrame(rows, columns=["question_id", "type", "verdict", "ours", "gold"])
    stats = {"n": len(df), "scored": n_scored, "ok": n_ok, "accuracy": round(n_ok / max(n_scored, 1), 3),
             "refusal_accuracy": round(ref_ok / max(len(df), 1), 3),
             "refusal_recall": round(tp / max(tp + fn, 1), 3), "refusal_precision": round(tp / max(tp + fp, 1), 3),
             "needs_review": int((df.verdict == "review").sum())}
    Path(out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(out_md).write_text("# Benchmark dev evaluation\n\n" + "\n".join(f"- {k}: {v}" for k, v in stats.items())
                            + "\n\n" + df.to_markdown(index=False), encoding="utf-8")
    return stats
