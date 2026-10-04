"""Run the system on every benchmark question and write the submission CSV.

The runner reads ONLY question_id, question_text and as_of_date. It never reads
should_refuse, metric_id, expected_tables or rubrics: the system answers as it would live.
Answers are written as produced; we do not edit them by hand (build-phase rule)."""
from __future__ import annotations
import csv, time
from pathlib import Path
import duckdb
import pandas as pd
from src.layer2.qa import QA

DEFAULT_COLS = ["question_id", "answer", "sql_or_sources", "refused"]


def _template_cols(cfg) -> list[str]:
    con = duckdb.connect(cfg["db_path"], read_only=True)
    try:
        cols = [c[0] for c in con.execute("DESCRIBE hidden.benchmark_answers_template").fetchall()]
        return cols or DEFAULT_COLS
    except duckdb.Error:
        return DEFAULT_COLS
    finally:
        con.close()


def load_questions(cfg, questions_csv: str | None = None, split: str | None = None) -> pd.DataFrame:
    if questions_csv:
        df = pd.read_csv(questions_csv, dtype=str)
    else:
        con = duckdb.connect(cfg["db_path"], read_only=True)
        df = con.execute("SELECT * FROM main.benchmark_questions").df().astype(str)
        con.close()
    if split and "split" in df.columns:
        df = df[df["split"].str.lower() == split.lower()]
    keep = [c for c in ("question_id", "question_text", "as_of_date") if c in df.columns]
    return df[keep]


def run(cfg, out: str, questions_csv: str | None = None, split: str | None = None,
        limit: int | None = None, resume: bool = True, pace_seconds: float = 0.0, log=print) -> str:
    qs = load_questions(cfg, questions_csv, split)
    if limit:
        qs = qs.head(limit)
    cols = _template_cols(cfg)
    out_p = Path(out)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if resume and out_p.exists():
        done = set(pd.read_csv(out_p, dtype=str)["question_id"])
    qa = QA(cfg)
    mode = "a" if done else "w"
    if not done:
        out_p.with_suffix(".timing.csv").write_text("question_id,seconds" + chr(10), encoding="utf-8")
    with open(out_p, mode, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        if not done:
            w.writeheader()
        for i, r in enumerate(qs.itertuples(index=False), 1):
            if r.question_id in done:
                continue
            if pace_seconds and i > 1:   # keep well under free-tier daily caps on long runs
                time.sleep(pace_seconds)
            t0 = time.time()
            as_of = getattr(r, "as_of_date", None)
            as_of = None if as_of in (None, "nan", "None", "") else as_of
            try:
                a = qa.answer(r.question_text, as_of)
            except Exception as e:  # keep going; the row records the failure honestly
                a = {"answer": f"error: {str(e)[:200]}", "sql_or_sources": "", "refused": False}
            row = {"question_id": r.question_id, "answer": a["answer"],
                   "sql_or_sources": a["sql_or_sources"], "refused": str(bool(a["refused"])).lower()}
            w.writerow(row)
            f.flush()
            with open(out_p.with_suffix(".timing.csv"), "a", encoding="utf-8") as tf:   # seconds per question
                tf.write(f"{r.question_id},{time.time() - t0:.2f}" + chr(10))
            # Windows consoles are often cp1252; strip non-ascii from the log line so one accented
            # character ("Montr\xe9al") doesn't crash the whole benchmark run.
            safe = row["answer"][:80].encode("ascii", "replace").decode("ascii")
            log(f"[{i}/{len(qs)}] {r.question_id} refused={row['refused']} {time.time()-t0:4.1f}s  {safe}")
    return str(out_p)
