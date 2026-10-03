"""Gateway falls back to the next free provider on a rate limit, and caches answers."""
import json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from src.layer2.llm import LLM

CALLS = {"limited": 0, "ok": 0}


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        name = self.path.split("/")[1]
        self.rfile.read(int(self.headers["Content-Length"]))
        CALLS[name] += 1
        if name == "limited":
            self.send_response(429); self.send_header("retry-after", "5"); self.end_headers(); return
        body = json.dumps({"choices": [{"message": {"content": '{"answer": "42"}'}}]}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def test_fallback_and_cache(tmp_path):
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    cfg = {"llm": {"cache_path": str(tmp_path / "c.sqlite"), "providers": [
        {"name": "a", "base_url": base + "/limited", "model": "m", "api_key_env": None, "rpm": 0},
        {"name": "b", "base_url": base + "/ok", "model": "m", "api_key_env": None, "rpm": 0}],
        "routes": {"default": ["a", "b"]}}}
    llm = LLM(cfg)
    assert llm.complete_json("s", "u")["answer"] == "42"
    assert CALLS == {"limited": 1, "ok": 1}
    assert llm.complete_json("s", "u")["answer"] == "42"      # served from cache
    assert CALLS == {"limited": 1, "ok": 1}
    srv.shutdown()


class FakeAudit:
    def __init__(self):
        self.events = []

    def write(self, event, **fields):
        self.events.append({"event": event, **fields})


class Overloaded(BaseHTTPRequestHandler):
    hits = 0

    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        Overloaded.hits += 1
        body = json.dumps([{"error": {"code": 503, "message": "This model is currently experiencing high demand."}}]).encode()
        self.send_response(503); self.send_header("retry-after", "7"); self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def test_503_retried_once_and_failures_audited(tmp_path, monkeypatch):
    import src.layer2.llm as llm_mod
    monkeypatch.setattr(llm_mod, "RETRY_503_AFTER_S", 0)
    bad = HTTPServer(("127.0.0.1", 0), Overloaded)
    good = HTTPServer(("127.0.0.1", 0), H)
    for s in (bad, good):
        threading.Thread(target=s.serve_forever, daemon=True).start()
    cfg = {"llm": {"cache_path": str(tmp_path / "c.sqlite"), "providers": [
        {"name": "gem", "base_url": f"http://127.0.0.1:{bad.server_port}", "model": "m", "api_key_env": None, "rpm": 0},
        {"name": "grq", "base_url": f"http://127.0.0.1:{good.server_port}/ok", "model": "m", "api_key_env": None, "rpm": 0}],
        "routes": {"default": ["gem", "grq"]}}}
    audit = FakeAudit()
    out = LLM(cfg, audit=audit).complete_json("s", "u2", purpose="plan")
    assert out["answer"] == "42"
    assert Overloaded.hits == 2                                  # first try + one retry
    failed = [e for e in audit.events if e["event"] == "llm_provider_failed"]
    assert len(failed) == 2 and all(e["provider"] == "gem" and e["http_status"] == 503 for e in failed)
    assert failed[-1]["cooldown_s"] == 7 and "high demand" in failed[-1]["error"]
    assert failed[-1]["purpose"] == "plan"
    assert [e["provider"] for e in audit.events if e["event"] == "llm_call"] == ["grq"]
    bad.shutdown(); good.shutdown()


class Echo(BaseHTTPRequestHandler):
    bodies = []

    def do_POST(self):
        Echo.bodies.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
        body = json.dumps({"choices": [{"message": {"content": '{"answer": "ok"}'}}]}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def test_reasoning_effort_per_purpose_and_cache_key(tmp_path):
    srv = HTTPServer(("127.0.0.1", 0), Echo)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    prov = {"name": "g", "base_url": base, "model": "m", "api_key_env": None, "rpm": 0,
            "reasoning_effort": {"plan": "medium", "answer": "low"}}
    cfg = {"llm": {"cache_path": str(tmp_path / "c.sqlite"), "providers": [prov], "routes": {"default": ["g"]}}}
    LLM(cfg).complete("s", "u", purpose="plan")
    LLM(cfg).complete("s", "u", purpose="other")           # no effort for this purpose: field not sent
    assert Echo.bodies[0]["reasoning_effort"] == "medium"
    assert "reasoning_effort" not in Echo.bodies[1]
    prov["reasoning_effort"] = {"plan": "low"}               # changed effort -> cache miss, new call
    LLM(cfg).complete("s", "u", purpose="plan")
    assert len(Echo.bodies) == 3 and Echo.bodies[2]["reasoning_effort"] == "low"
    LLM(cfg).complete("s", "u", purpose="plan")              # same settings -> cached
    assert len(Echo.bodies) == 3
    srv.shutdown()


class TooMany(BaseHTTPRequestHandler):
    hits = 0

    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        TooMany.hits += 1
        if TooMany.hits <= 2:
            body = json.dumps({"error": {"message": "rate limit"}}).encode()
            self.send_response(429); self.send_header("retry-after", "1"); self.end_headers()
            self.wfile.write(body)
            return
        body = json.dumps({"choices": [{"message": {"content": '{"answer": "ok"}'}}]}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def test_waits_for_cooldown_when_every_provider_is_limited(tmp_path, monkeypatch):
    import src.layer2.llm as llm_mod
    monkeypatch.setattr(llm_mod, "MAX_WAIT_S", 3.0)   # bound the wait in tests
    TooMany.hits = 0
    srv = HTTPServer(("127.0.0.1", 0), TooMany)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    cfg = {"llm": {"cache_path": str(tmp_path / "c.sqlite"), "providers": [
        {"name": "a", "base_url": base + "/a", "model": "m", "api_key_env": None, "rpm": 0},
        {"name": "b", "base_url": base + "/b", "model": "m", "api_key_env": None, "rpm": 0}],
        "routes": {"default": ["a", "b"]}}}
    audit = FakeAudit()
    out = LLM(cfg, audit=audit).complete_json("s", "u-wait", purpose="plan")
    assert out["answer"] == "ok"
    # 2 providers rate-limited on first pass, then wait, then one succeeds on second pass
    assert TooMany.hits == 3
    failed = [e for e in audit.events if e["event"] == "llm_provider_failed"]
    assert len(failed) == 2 and {e["provider"] for e in failed} == {"a", "b"}
    srv.shutdown()
