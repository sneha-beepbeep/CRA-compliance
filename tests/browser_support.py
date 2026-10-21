"""Live app for browser tests (tests/e2e, tests/a11y/test_axe.py).

pytest-django's live_server flushes with TRUNCATE, which the append-only audit
table correctly refuses. Instead each browser session gets its own committed
database (<name>_browser_<pid>), migrated and seeded via manage.py, served by a
dev-server subprocess, and dropped afterwards. Needs DATABASE_URL (a role that
may CREATE DATABASE), Playwright and its Chromium build.
"""
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pytest

ROOT = Path(__file__).resolve().parents[1]


def require_browser():
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("postgres: DATABASE_URL not set")
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        pytest.skip("Playwright not installed (uv sync --group browser)")


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_app():
    require_browser()
    import psycopg
    base = urlparse(os.environ["DATABASE_URL"])
    name = f"{base.path.lstrip('/')}_browser_{os.getpid()}"
    db_url = urlunparse(base._replace(path="/" + name))
    with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as c:
        c.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        c.execute(f'CREATE DATABASE "{name}"')
    env = {**os.environ, "DATABASE_URL": db_url, "DJANGO_SETTINGS_MODULE": "tracker.settings.dev"}
    py = sys.executable
    for cmd in (["migrate", "-v0"], ["seed_dev"]):
        subprocess.run([py, "manage.py", *cmd], cwd=ROOT, env=env, check=True, capture_output=True)
    port = _free_port()
    server = subprocess.Popen([py, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"], cwd=ROOT, env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            try:
                urllib.request.urlopen(url + "/sign-in/", timeout=1)
                break
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError("dev server did not start")
        yield {"url": url, "db_url": db_url}
    finally:
        server.terminate()
        server.wait(timeout=10)
        with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as c:
            c.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


@pytest.fixture(scope="session")
def browser():
    require_browser()
    from playwright.sync_api import Error, sync_playwright
    with sync_playwright() as p:
        try:
            b = p.chromium.launch(channel=os.environ.get("PLAYWRIGHT_CHANNEL", "chromium"))
        except Error as e:
            pytest.skip(f"Chromium not installed (playwright install chromium): {str(e).splitlines()[0]}")
        yield b
        b.close()


def sign_in(page, base, email="responder@acme.example"):
    page.goto(base + "/dev/login/")
    page.select_option("#email", email)
    page.click("button.primary")
    page.wait_for_url(base + "/")


def h_scroll(page) -> bool:
    return page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
