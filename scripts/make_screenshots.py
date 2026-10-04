"""Captures three Agent Desk screenshots for the README.

  python scripts/make_screenshots.py

Launches Streamlit headless on port 8502, opens the case screen (hero case), the ask box, and
the supervisor queue, saves PNGs under docs/screenshots/."""
from __future__ import annotations
import subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

HERO = "CS-2026-134197"
OUT = Path("docs/screenshots")
PORT = 8502


def _wait_ready(url: str, timeout_s: int = 60):
    import urllib.request
    for _ in range(timeout_s * 2):
        try:
            if urllib.request.urlopen(url + "/_stcore/health", timeout=2).status == 200:
                return
        except Exception:
            time.sleep(0.5)
    raise TimeoutError(f"streamlit not ready at {url}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    import os
    env = os.environ.copy()
    env.update({"PYTHONPATH": ".", "PYTHONIOENCODING": "utf-8",
                "STREAMLIT_SERVER_HEADLESS": "true", "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false"})
    proc = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app/streamlit_app.py",
                             f"--server.port={PORT}", "--server.address=127.0.0.1",
                             "--server.headless=true"], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        base = f"http://127.0.0.1:{PORT}"
        _wait_ready(base)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": 1600, "height": 1200})
            # 1) Case screen (hero case opens by default)
            page = ctx.new_page()
            page.goto(base)
            page.wait_for_selector("h1:has-text('Agent Desk')", timeout=30000)
            page.wait_for_timeout(2500)         # allow lazy caches to settle
            page.screenshot(path=str(OUT / "01_case_screen.png"), full_page=True)
            # 2) Ask box
            page.get_by_text("Ask", exact=False).first.click()
            page.wait_for_selector("input[aria-label='Question']", timeout=10000)
            page.fill("input[aria-label='Question']", "How many open collections cases are there?")
            page.get_by_role("button", name="Ask").click()
            page.wait_for_selector("text=Answer", timeout=120000)
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT / "02_ask_box.png"), full_page=True)
            # 3) Supervisor queue
            page.get_by_text("Supervisor queue", exact=False).first.click()
            page.wait_for_selector("text=Supervisor queue", timeout=10000)
            page.wait_for_timeout(2000)
            page.screenshot(path=str(OUT / "03_supervisor_queue.png"), full_page=True)
            browser.close()
        for p in OUT.glob("*.png"):
            print(f"  {p}  ({p.stat().st_size // 1024} KB)")
    finally:
        proc.terminate()
        try: proc.wait(timeout=5)
        except Exception: proc.kill()


if __name__ == "__main__":
    main()
