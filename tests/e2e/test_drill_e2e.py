"""Browser end-to-end flows (drill: log -> strip -> filings -> close) with Playwright.

The same flow runs headless over HTTP in tests/integration/test_flows.py. The
browser version (countdown JS, tab title, 320 px reflow) needs Playwright.
"""
import pytest

pytest.importorskip("playwright", reason="Playwright not installed; browser e2e runs in CI")
