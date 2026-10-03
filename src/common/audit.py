"""Append-only audit log (JSON lines). Every LLM call, query, answer and refusal goes here."""
from __future__ import annotations
import json, time, uuid
from pathlib import Path


class AuditLog:
    def __init__(self, path: str):
        self.path = Path(path)

    def write(self, event: str, **fields) -> str:
        rec = {"id": str(uuid.uuid4()), "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": event, **fields}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        return rec["id"]
