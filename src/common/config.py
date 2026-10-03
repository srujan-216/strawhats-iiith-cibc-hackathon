"""Config loading. One place for paths so every layer agrees."""
from __future__ import annotations
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | Path | None = None) -> dict:
    cfg_path = Path(path) if path else ROOT / "config.yaml"
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)
    cfg["data_dir"] = str((ROOT / cfg["data_dir"]).resolve()) if not Path(cfg["data_dir"]).is_absolute() else cfg["data_dir"]
    cfg["db_path"] = str(ROOT / cfg["db_path"])
    cfg["audit_log"] = str(ROOT / cfg["audit_log"])
    cfg["llm"]["cache_path"] = str(ROOT / cfg["llm"].get("cache_path", "warehouse/llm_cache.sqlite"))
    Path(cfg["db_path"]).parent.mkdir(parents=True, exist_ok=True)
    Path(cfg["audit_log"]).parent.mkdir(parents=True, exist_ok=True)
    return cfg
