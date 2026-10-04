"""Ping each (provider, model) in config.yaml with a 10-token request. Reports status per model.

  python scripts/check_providers.py

Does not use the gateway's cache or audit log; a bare HTTP POST so what you see is what you'll
hit at bench time. Costs 1-2 tokens per model; safe to run before a quota-sensitive benchmark."""
from __future__ import annotations
import os, sys, time
import requests
from src.common.config import load_config


def ping(base_url: str, api_key: str | None, model: str, timeout_s: int = 10):
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    body = {"model": model, "max_tokens": 10, "temperature": 0,
            "messages": [{"role": "user", "content": "ping"}]}
    t0 = time.time()
    try:
        r = requests.post(url, headers=headers, json=body, timeout=timeout_s)
    except requests.Timeout:
        return {"status": "TIMEOUT", "code": None, "ms": int(1000 * timeout_s), "detail": ""}
    except requests.RequestException as e:
        return {"status": "NET_ERR", "code": None, "ms": int(1000 * (time.time() - t0)),
                "detail": str(e)[:120]}
    ms = int(1000 * (time.time() - t0))
    if r.status_code == 200:
        return {"status": "OK", "code": 200, "ms": ms, "detail": ""}
    txt = r.text[:300].replace("\n", " ")
    try:
        import json as _j
        err = _j.loads(r.text)
        err = err[0] if isinstance(err, list) else err
        txt = (err.get("error", {}) or {}).get("message", txt)
    except Exception:
        pass
    return {"status": {404: "NOT_FOUND", 429: "RATE_LIMIT", 401: "AUTH"}.get(r.status_code, f"HTTP_{r.status_code}"),
            "code": r.status_code, "ms": ms, "detail": str(txt)[:140]}


def main():
    cfg = load_config()
    print(f"{'provider':10s}  {'model':35s}  {'status':12s}  {'ms':>5s}  detail")
    print("-" * 110)
    overall_ok = True
    for p in cfg["llm"]["providers"]:
        api_key = os.environ.get(p.get("api_key_env", ""), "") if p.get("api_key_env") else None
        if p.get("api_key_env") and not api_key:
            print(f"{p['name']:10s}  {'<any>':35s}  {'NO_KEY':12s}  {'-':>5s}  env {p['api_key_env']} unset; provider will be skipped")
            continue
        models = [p["model"], *p.get("fallback_models", [])]
        for m in models:
            r = ping(p["base_url"], api_key, m)
            if r["status"] != "OK":
                overall_ok = False
            print(f"{p['name']:10s}  {m:35s}  {r['status']:12s}  {r['ms']:>5d}  {r['detail'][:140]}")
    sys.exit(0 if overall_ok else 1)


if __name__ == "__main__":
    main()
