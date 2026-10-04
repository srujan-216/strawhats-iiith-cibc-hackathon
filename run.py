"""Straw Hats - Collections 360. One entry point for every step.

  python run.py register            # load all source files into DuckDB (raw + typed)
  python run.py profile [--sample N] # reports/profile.md
  python run.py silver [--sample N]  # cleaned silver.* tables + silver.fix_log
  python run.py match  [--sample N]  # id_xref (golden_id) + reports/match_report.md
  python run.py c360                 # gold.c360_customer / c360_account / c360_case / field_trust + dq_results
  python run.py dq-report            # reports/data_quality_report.md
  python run.py all    [--sample N]  # register -> silver -> match -> c360 -> dq-report
  python run.py ask "question" [--as-of 2026-09-28]
  python run.py bench [--split dev] [--questions extra.csv] [--out submission/benchmark_answers.csv]
  python run.py eval [--answers submission/benchmark_answers_dev.csv]
"""
from __future__ import annotations
import argparse, json, sys
from src.common.config import load_config


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", default=None)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("register"); r.add_argument("--no-materialise", action="store_true")
    pr = sub.add_parser("profile"); pr.add_argument("--sample", type=int, default=None)
    sv = sub.add_parser("silver"); sv.add_argument("--sample", type=int, default=None)
    sv.add_argument("--tables", nargs="*", default=None, help="subset of tables (default: all)")
    mt = sub.add_parser("match"); mt.add_argument("--sample", type=int, default=None)
    sub.add_parser("c360")
    sub.add_parser("dq-report")
    ft = sub.add_parser("features"); ft.add_argument("--sample", type=int, default=None)
    ft.add_argument("--dates", nargs="*", default=None, help="decision_dates (default: SNAPSHOT_DATE)")
    sub.add_parser("text-features")   # train 6 classifiers + score all notes/transcripts
    sub.add_parser("feature-report")  # reports/feature_report.md
    sub.add_parser("randomisation-check")  # P6 pre-flight: test_cell balance
    sub.add_parser("train")                # fit 6 LightGBM NBA classifiers
    sub.add_parser("score")                # batch-score all open cases -> gold.nba_recommendations
    sc = sub.add_parser("score-case"); sc.add_argument("case_id")
    sub.add_parser("app")                  # launch Streamlit Agent Desk
    sub.add_parser("fairness")             # reports/fairness_report.md + model card append
    al = sub.add_parser("all")
    al.add_argument("--sample", type=int, default=None, help="pass to each stage (optional)")
    a = sub.add_parser("ask"); a.add_argument("question"); a.add_argument("--as-of", default=None)
    b = sub.add_parser("bench")
    b.add_argument("--split", default=None); b.add_argument("--questions", default=None)
    b.add_argument("--out", default="submission/benchmark_answers.csv"); b.add_argument("--limit", type=int)
    b.add_argument("--fresh", action="store_true", help="ignore existing rows in --out")
    b.add_argument("--pace-seconds", type=float, default=0.0,
                   help="sleep N seconds between questions (default 0; use 5 for the 19:00 extras run)")
    e = sub.add_parser("eval"); e.add_argument("--answers", default="submission/benchmark_answers_dev.csv")
    args = p.parse_args(argv)
    cfg = load_config(args.config)

    if args.cmd == "register":
        from src.layer1.register import register_all
        register_all(cfg, materialise=not args.no_materialise).close()
    elif args.cmd == "profile":
        import duckdb
        from src.layer1.profile import profile
        con = duckdb.connect(cfg["db_path"], read_only=True)
        print(profile(con, "reports/profile.md", args.sample))
    elif args.cmd == "silver":
        import duckdb
        from tabulate import tabulate
        from src.layer1.silver import run_silver, fix_log_summary, write_fix_log_report
        run_silver(cfg, args.sample, args.tables)
        con = duckdb.connect(cfg["db_path"], read_only=True)
        rows = [(t, r, f"{n:,}", f"{100 * n / max(i, 1):.2f}%", (b or "")[:40], (a or "")[:40])
                for t, r, n, i, b, a in fix_log_summary(con)]
        print(tabulate(rows, headers=["table", "rule", "rows", "% of rows in", "example before", "example after"]))
        print(write_fix_log_report(con))
    elif args.cmd == "match":
        from src.layer1.match import run_match
        print(json.dumps(run_match(cfg, args.sample), indent=2))
    elif args.cmd == "c360":
        from src.layer1.c360 import build_c360
        print(json.dumps(build_c360(cfg), indent=2))
    elif args.cmd == "dq-report":
        from src.layer1.dq_report import write_dq_report
        print(write_dq_report(cfg))
    elif args.cmd == "features":
        from src.layer3.features import build_offline
        print(json.dumps(build_offline(cfg, args.dates, args.sample), indent=2))
    elif args.cmd == "text-features":
        from src.layer3.text_classifier import train_and_score
        train_and_score(cfg)
    elif args.cmd == "feature-report":
        from src.layer3.feature_report import build_report
        print(build_report(cfg))
    elif args.cmd == "randomisation-check":
        from src.layer4.randomisation import write_report
        print(json.dumps(write_report(cfg), indent=2))
    elif args.cmd == "train":
        from src.layer4.nba import train
        print(json.dumps(train(cfg), indent=2, default=str))
    elif args.cmd == "score":
        from src.layer4.nba import batch_score
        print(batch_score(cfg))
    elif args.cmd == "score-case":
        from src.layer4.nba import score_case
        print(json.dumps(score_case(cfg, args.case_id), indent=2, default=str))
    elif args.cmd == "app":
        import subprocess
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app/streamlit_app.py",
                        "--server.headless=true"])
    elif args.cmd == "fairness":
        from src.governance.fairness import write_report, append_to_model_card
        verdicts = write_report(cfg)
        append_to_model_card(verdicts)
        print(json.dumps(verdicts, indent=2))
    elif args.cmd == "all":
        import time
        from src.layer1.register import register_all
        from src.layer1.silver import run_silver
        from src.layer1.match import run_match
        from src.layer1.c360 import build_c360
        from src.layer1.dq_report import write_dq_report
        t = time.time(); print("== register"); register_all(cfg).close()
        print(f"== silver (sample={args.sample})"); run_silver(cfg, args.sample)
        print(f"== match (sample={args.sample})"); run_match(cfg, args.sample)
        print("== c360"); build_c360(cfg)
        print("== dq-report"); print(write_dq_report(cfg))
        print(f"all stages done in {(time.time()-t)/60:.1f} min")
    elif args.cmd == "ask":
        from src.layer2.qa import QA
        print(json.dumps(QA(cfg).answer(args.question, args.as_of), indent=2, default=str))
    elif args.cmd == "bench":
        from src.layer2.benchmark import run
        print(run(cfg, args.out, args.questions, args.split, args.limit,
                  resume=not args.fresh, pace_seconds=args.pace_seconds))
    elif args.cmd == "eval":
        from src.layer2.evaluate import evaluate
        print(json.dumps(evaluate(cfg, args.answers, "reports/benchmark_dev_eval.md"), indent=2))


if __name__ == "__main__":
    sys.exit(main())
