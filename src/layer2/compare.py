"""Run the dev benchmark under several LLM configs and print one comparison table.

  python -m src.layer2.compare            # configs A, B, C (see CONFIGS)

Each config gets its own output CSV (submissions/benchmark_answers_dev_<name>.csv, git-ignored), is run
with a fresh start, and is scored by evaluate.py. Provider mix comes from the audit log lines written
during the run (cached calls are counted separately)."""
from __future__ import annotations
import copy, json, statistics, time
from pathlib import Path
import pandas as pd
from src.common.config import load_config
from src.layer2.benchmark import run
from src.layer2.evaluate import evaluate

EFFORT_B = {"plan": "medium", "sql_fix": "medium", "answer": "low", "answer_docs": "low"}
CONFIGS = {   # name -> (gemini model or None = as in config.yaml, gemini reasoning_effort)
    "A": (None, None),
    "B": (None, EFFORT_B),
    "C": ("gemini-3.5-flash", EFFORT_B),
}


def _gemini(cfg):
    return next(p for p in cfg["llm"]["providers"] if p["name"] == "gemini")


def run_config(base: dict, name: str, model, effort, log=print) -> dict:
    cfg = copy.deepcopy(base)
    g = _gemini(cfg)
    if model:
        g["model"] = model
    g["reasoning_effort"] = effort
    out = f"submissions/benchmark_answers_dev_{name}.csv"
    audit = Path(cfg["audit_log"])
    offset = audit.stat().st_size if audit.exists() else 0
    t0 = time.time()
    run(cfg, out, split="dev", resume=False, log=lambda *_: None)
    total = time.time() - t0
    stats = evaluate(cfg, out, f"reports/benchmark_dev_eval_{name}.md")
    mix, failed = {}, 0
    with open(audit, "rb") as f:
        f.seek(offset)
        for line in f:
            e = json.loads(line)
            if e["event"] == "llm_call":
                k = e["provider"] + ("(cached)" if e.get("cached") else "")
                mix[k] = mix.get(k, 0) + 1
            elif e["event"] == "llm_provider_failed":
                failed += 1
    secs = pd.read_csv(Path(out).with_suffix(".timing.csv"))["seconds"]
    res = {"config": name, "model": _gemini(cfg)["model"], "effort": json.dumps(effort) if effort else "default",
           **stats, "total_s": round(total), "median_s": round(statistics.median(secs), 1),
           "provider_mix": ", ".join(f"{k} {v}" for k, v in sorted(mix.items())), "provider_failures": failed}
    log(json.dumps(res))
    return res


if __name__ == "__main__":
    base = load_config()
    results = [run_config(base, n, m, e) for n, (m, e) in CONFIGS.items()]
    df = pd.DataFrame(results)
    Path("reports").mkdir(exist_ok=True)
    Path("reports/l2_effort_comparison.md").write_text(df.to_markdown(index=False), encoding="utf-8")
    print(df.to_markdown(index=False))
