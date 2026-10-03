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
