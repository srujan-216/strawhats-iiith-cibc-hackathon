"""Straw Hats - Collections 360. One entry point for every step.

  python run.py register            # load all source files into DuckDB (raw + typed)
  python run.py profile [--sample N] # reports/profile.md
  python run.py ask "question" [--as-of 2026-09-28]
  python run.py bench [--split dev] [--questions extra.csv] [--out submissions/benchmark_answers.csv]
  python run.py eval [--answers submissions/benchmark_answers_dev.csv]
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
    a = sub.add_parser("ask"); a.add_argument("question"); a.add_argument("--as-of", default=None)
    b = sub.add_parser("bench")
    b.add_argument("--split", default=None); b.add_argument("--questions", default=None)
    b.add_argument("--out", default="submissions/benchmark_answers.csv"); b.add_argument("--limit", type=int)
    b.add_argument("--fresh", action="store_true", help="ignore existing rows in --out")
    e = sub.add_parser("eval"); e.add_argument("--answers", default="submissions/benchmark_answers_dev.csv")
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
    elif args.cmd == "ask":
        from src.layer2.qa import QA
        print(json.dumps(QA(cfg).answer(args.question, args.as_of), indent=2, default=str))
    elif args.cmd == "bench":
        from src.layer2.benchmark import run
        print(run(cfg, args.out, args.questions, args.split, args.limit, resume=not args.fresh))
    elif args.cmd == "eval":
        from src.layer2.evaluate import evaluate
        print(json.dumps(evaluate(cfg, args.answers, "reports/benchmark_dev_eval.md"), indent=2))


if __name__ == "__main__":
    sys.exit(main())
