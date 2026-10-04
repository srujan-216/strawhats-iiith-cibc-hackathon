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
MAX_WAIT_S = 75.0   # how long complete() will wait when every provider is cooling down


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
        # cache key includes each candidate provider's model and reasoning effort for this purpose,
        # so changing either never returns a stale answer
        knobs = [(p["name"], p.get("model"), self._effort(p, purpose)) for p in self._route_providers()]
        key = hashlib.sha256(json.dumps([self.route, system, user, knobs]).encode()).hexdigest()
        hit = self.cache.get(key)
        if hit:
            self._audit(purpose, hit[1], 0.0, len(system) + len(user), len(hit[0]), cached=True)
            return hit[0]
        errors = []
        # Two passes: first try any provider that is not cooling down; if every provider is on cool-down,
        # wait for the earliest one (up to MAX_WAIT_S) so one 429 burst does not kill a batch run.
        for attempt in (1, 2):
            for p in self._providers():
                try:
                    t0 = time.time()
                    out = self._call(p, system, user, purpose)
                    self.cache.put(key, out, p["name"])
                    self._audit(purpose, p["name"], time.time() - t0, len(system) + len(user), len(out))
                    return out
                except ProviderUnavailable as e:
                    errors.append(f"{p['name']}: {e}")
                    if self.audit:
                        self.audit.write("llm_provider_failed", purpose=purpose, route=self.route,
                                         provider=p["name"], http_status=e.status, error=str(e)[:200],
                                         cooldown_s=round(e.cooldown_s))
            if attempt == 1 and self._wait_for_cooldown():
                continue
            break
        raise RuntimeError("all LLM providers unavailable: " + " | ".join(errors))

    def _wait_for_cooldown(self) -> bool:
        """Wait up to MAX_WAIT_S for the earliest cooling-down provider in this route to recover.
        Returns True if we waited (caller should retry), False if there is nothing to wait for."""
        now = time.time()
        waits = [self._cooldown_until.get(p["name"], 0) - now
                 for p in self._route_providers()
                 if not (p.get("api_key_env") and not os.environ.get(p["api_key_env"]))]
        waits = [w for w in waits if w > 0]
        if not waits:
            return False
        delay = min(min(waits), MAX_WAIT_S)
        if delay <= 0:
            return False
        time.sleep(delay)
        return True

    def complete_json(self, system: str, user: str, purpose: str = "") -> dict:
        raw = self.complete(system + "\nRespond with one JSON object only. No markdown fences.", user, purpose)
        return parse_json(raw)

    # ------------------------------------------------------------------ internals
    @staticmethod
    def _effort(p: dict, purpose: str) -> str | None:
        """reasoning_effort for this provider and purpose: a string (all purposes) or a
        {purpose: level, default: level} map in config.yaml. None = provider default (not sent)."""
        e = p.get("reasoning_effort")
        if isinstance(e, dict):
            e = e.get(purpose, e.get("default"))
        return e or None

    def _route_providers(self) -> list[dict]:
        names = self.c.get("routes", {}).get(self.route) or [p["name"] for p in self.c["providers"]]
        by_name = {p["name"]: p for p in self.c["providers"]}
        return [by_name[n] for n in names if n in by_name]

    def _providers(self) -> list[dict]:
        out = []
        for p in self._route_providers():
            n = p["name"]
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

    def _call(self, p: dict, system: str, user: str, purpose: str = "") -> str:
        """One provider call. If 429 and the provider lists `fallback_models`, retry the same provider
        on each fallback model in turn before cooling the provider down and raising."""
        import requests
        self._pace(p)
        headers = {"Content-Type": "application/json"}
        if p.get("api_key_env"):
            headers["Authorization"] = f"Bearer {os.environ[p['api_key_env']]}"
        effort = self._effort(p, purpose)
        url = p["base_url"].rstrip("/") + "/chat/completions"
        models = [p["model"], *p.get("fallback_models", [])]
        last_err = None
        for mi, model in enumerate(models):
            body = {"model": model, "temperature": self.c.get("temperature", 0),
                    "max_tokens": self.c.get("max_tokens", 1500),
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
            if effort:
                body["reasoning_effort"] = effort
            for attempt in (1, 2):   # 503 retry on the same model
                try:
                    r = requests.post(url, headers=headers, json=body, timeout=p.get("timeout_s", 120))
                except requests.RequestException as e:
                    self._cooldown_until[p["name"]] = time.time() + 30
                    raise ProviderUnavailable(f"network: {str(e)[:120]}", None, 30)
                if r.status_code == 503 and attempt == 1:
                    if self.audit:
                        self.audit.write("llm_provider_failed", route=self.route, provider=p["name"],
                                         http_status=503, error=f"overloaded on {model}; retrying once",
                                         cooldown_s=0)
                    time.sleep(RETRY_503_AFTER_S)
                    continue
                break
            # Fallback triggers: 429 (quota), 5xx (server problem), 404 (model retired/renamed),
            # or body says "quota". For any of these, try the next model in the chain before
            # cooling the whole provider down.
            retryable = (r.status_code == 429 or r.status_code == 404 or r.status_code >= 500
                         or "quota" in r.text[:500].lower())
            if retryable:
                retry = min(float(r.headers.get("retry-after", 60) or 60), 600)
                last_err = ProviderUnavailable(
                    f"HTTP {r.status_code} on {model}: {_short(r.text)} (cool-down {retry:.0f}s)",
                    r.status_code, retry)
                if mi < len(models) - 1:
                    if self.audit:
                        self.audit.write("llm_provider_failed", route=self.route, provider=p["name"],
                                         http_status=r.status_code, error=f"{model}; falling back",
                                         cooldown_s=0)
                    continue
                # 404 means the final fallback model is invalid: don't put the provider on a long
                # cool-down for that (nothing will fix it); 429/5xx deserve the usual cool-down
                if r.status_code == 404:
                    raise last_err
                self._cooldown_until[p["name"]] = time.time() + retry
                raise last_err
            if r.status_code >= 400:
                raise ProviderUnavailable(f"HTTP {r.status_code} on {model}: {_short(r.text)}", r.status_code, 0)
            data = r.json()
            return data["choices"][0]["message"]["content"] or ""
        raise last_err or ProviderUnavailable("unknown error", None, 0)

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
