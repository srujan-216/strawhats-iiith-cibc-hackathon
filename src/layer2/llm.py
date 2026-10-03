"""Model gateway: every LLM call in the system goes through here. Free providers only.

- One OpenAI-compatible client for all providers: Google AI Studio (Gemini free tier), Groq free tier,
  and our own local model (vLLM or Ollama on the team GPU). No paid APIs.
- Providers are tried in order. On a rate limit (429), quota error, timeout or 5xx the provider is put
  on cool-down and the next one is tried, so free-tier limits never stop a benchmark run.
  A 503 ("model overloaded") is retried once on the same provider after 3 s before falling back.
  Every failed attempt is audited as `llm_provider_failed` so we can see why a provider was skipped.
- A per-provider pacer keeps us under each free tier's requests-per-minute.
- Responses are cached on disk (SQLite) by prompt hash: reruns cost no quota and give identical answers.
- Optional PII redaction before a prompt leaves the process; every call is audited.
"""
from __future__ import annotations
import hashlib, json, os, re, sqlite3, threading, time
from pathlib import Path
from typing import Callable

_PII = [
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "[EMAIL]"),
    (re.compile(r"\+?1?[\s\-.(]*\d{3}[\s\-.)]*\d{3}[\s\-.]*\d{4}\b"), "[PHONE]"),
    (re.compile(r"\b[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d\b"), "[POSTAL]"),
]


def redact(text: str) -> str:
    for rx, rep in _PII:
        text = rx.sub(rep, text)
    return text


class _Cache:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS c (k TEXT PRIMARY KEY, v TEXT, provider TEXT, ts REAL)")
        self.lock = threading.Lock()

    def get(self, k):
        with self.lock:
            r = self.db.execute("SELECT v, provider FROM c WHERE k=?", (k,)).fetchone()
        return r

    def put(self, k, v, provider):
        with self.lock:
            self.db.execute("INSERT OR REPLACE INTO c VALUES (?,?,?,?)", (k, v, provider, time.time()))
            self.db.commit()


class ProviderUnavailable(Exception):
    def __init__(self, msg: str, status: int | None = None, cooldown_s: float = 0.0):
        super().__init__(msg)
        self.status = status
        self.cooldown_s = cooldown_s


RETRY_503_AFTER_S = 3.0


class LLM:
    def __init__(self, cfg: dict, audit=None, mock: Callable[[str, str], str] | None = None,
                 route: str = "default"):
        self.c = cfg["llm"]
        self.audit = audit
        self.mock = mock
        self.route = route
        self.cache = None if mock else _Cache(self.c.get("cache_path", "warehouse/llm_cache.sqlite"))
        self._last_call: dict[str, float] = {}
        self._cooldown_until: dict[str, float] = {}

    # ------------------------------------------------------------------ public
    def complete(self, system: str, user: str, purpose: str = "") -> str:
        if self.c.get("redact_pii"):
            user = redact(user)
        if self.mock:
            return self.mock(system, user)
        key = hashlib.sha256(json.dumps([self.route, system, user]).encode()).hexdigest()
        hit = self.cache.get(key)
        if hit:
            self._audit(purpose, hit[1], 0.0, len(system) + len(user), len(hit[0]), cached=True)
            return hit[0]
        errors = []
        for p in self._providers():
            try:
                t0 = time.time()
                out = self._call(p, system, user)
                self.cache.put(key, out, p["name"])
                self._audit(purpose, p["name"], time.time() - t0, len(system) + len(user), len(out))
                return out
            except ProviderUnavailable as e:
                errors.append(f"{p['name']}: {e}")
                if self.audit:
                    self.audit.write("llm_provider_failed", purpose=purpose, route=self.route,
                                     provider=p["name"], http_status=e.status, error=str(e)[:200],
                                     cooldown_s=round(e.cooldown_s))
        raise RuntimeError("all LLM providers unavailable: " + " | ".join(errors))

    def complete_json(self, system: str, user: str, purpose: str = "") -> dict:
        raw = self.complete(system + "\nRespond with one JSON object only. No markdown fences.", user, purpose)
        return parse_json(raw)

    # ------------------------------------------------------------------ internals
    def _providers(self) -> list[dict]:
        names = self.c.get("routes", {}).get(self.route) or [p["name"] for p in self.c["providers"]]
        by_name = {p["name"]: p for p in self.c["providers"]}
        out = []
        for n in names:
            p = by_name.get(n)
            if not p:
                continue
            if p.get("api_key_env") and not os.environ.get(p["api_key_env"]):
                continue  # no key configured on this machine: skip silently
            if time.time() < self._cooldown_until.get(n, 0):
                continue
            out.append(p)
        return out

    def _pace(self, p: dict):
        rpm = p.get("rpm") or 0
        if rpm <= 0:
            return
        gap = 60.0 / rpm
        wait = self._last_call.get(p["name"], 0) + gap - time.time()
        if wait > 0:
            time.sleep(wait)
        self._last_call[p["name"]] = time.time()

    def _call(self, p: dict, system: str, user: str) -> str:
        import requests
        self._pace(p)
        headers = {"Content-Type": "application/json"}
        if p.get("api_key_env"):
            headers["Authorization"] = f"Bearer {os.environ[p['api_key_env']]}"
        body = {"model": p["model"], "temperature": self.c.get("temperature", 0),
                "max_tokens": self.c.get("max_tokens", 1500),
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        url = p["base_url"].rstrip("/") + "/chat/completions"
        for attempt in (1, 2):
            try:
                r = requests.post(url, headers=headers, json=body, timeout=p.get("timeout_s", 120))
            except requests.RequestException as e:
                self._cooldown_until[p["name"]] = time.time() + 30
                raise ProviderUnavailable(f"network: {str(e)[:120]}", None, 30)
            if r.status_code == 503 and attempt == 1:   # overloaded: often clears in seconds
                if self.audit:
                    self.audit.write("llm_provider_failed", route=self.route, provider=p["name"],
                                     http_status=503, error="overloaded; retrying once", cooldown_s=0)
                time.sleep(RETRY_503_AFTER_S)
                continue
            break
        if r.status_code == 429 or r.status_code >= 500 or "quota" in r.text[:500].lower():
            retry = min(float(r.headers.get("retry-after", 60) or 60), 600)
            self._cooldown_until[p["name"]] = time.time() + retry
            raise ProviderUnavailable(f"HTTP {r.status_code}: {_short(r.text)} (cool-down {retry:.0f}s)",
                                      r.status_code, retry)
        if r.status_code >= 400:
            raise ProviderUnavailable(f"HTTP {r.status_code}: {_short(r.text)}", r.status_code, 0)
        data = r.json()
        return data["choices"][0]["message"]["content"] or ""

    def _audit(self, purpose, provider, latency, pchars, ochars, cached=False):
        if self.audit:
            self.audit.write("llm_call", purpose=purpose, route=self.route, provider=provider,
                             latency_s=round(latency, 2), prompt_chars=pchars, output_chars=ochars, cached=cached)


def _short(text: str) -> str:
    """Provider error message in one short line (OpenAI-style {"error": {"message": ...}} if present)."""
    try:
        err = json.loads(text)
        err = err[0] if isinstance(err, list) else err
        msg = err.get("error", {}).get("message") or text
    except (ValueError, AttributeError):
        msg = text
    return " ".join(str(msg).split())[:150]


def parse_json(raw: str) -> dict:
    txt = re.sub(r"<think>.*?</think>", "", raw, flags=re.S)          # reasoning models
    txt = re.sub(r"^```(?:json)?|```$", "", txt.strip(), flags=re.M).strip()
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", txt, flags=re.S)
        if m:
            return json.loads(m.group(0))
        raise
