"""Browser end-to-end drill at 320 px (P4): log -> preview -> strip and tab title ->
record a filing -> close as not reportable -> leaves the strip. No sideways scroll."""
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("playwright", reason="Playwright not installed (uv sync --group browser)")
from playwright.sync_api import expect

from tests.browser_support import h_scroll, sign_in

pytestmark = [pytest.mark.postgres, pytest.mark.browser]


def test_drill_flow_on_a_phone(browser, live_app):  # noqa: F811
    base = live_app["url"]
    ctx = browser.new_context(viewport={"width": 320, "height": 740})
    page = ctx.new_page()
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    missing = []
    page.on("response", lambda r: missing.append(r.url) if r.status == 404 else None)
    sign_in(page, base)

    aw = datetime.now(timezone.utc).replace(second=0, microsecond=0) - timedelta(hours=1)
    page.goto(base + "/events/log?drill=1")
    assert not h_scroll(page)
    page.check("input[name=event_type][value=vulnerability]")
    page.fill("#id_awareness_date", aw.strftime("%Y-%m-%d"))
    page.fill("#id_awareness_time", aw.strftime("%H:%M"))
    page.select_option("#id_awareness_tz", "UTC")
    page.locator("#id_awareness_tz").dispatch_event("change")
    # QA-06: preview from type + awareness before the rest of the form is filled
    due = (aw + timedelta(hours=24)).strftime("%H:%M UTC")
    expect(page.locator("#preview")).to_contain_text(due)  # string-eval waits are blocked by our CSP
    page.select_option("#id_product", index=1)
    page.fill("#id_title", "Phone drill")
    page.click("text=Log drill and start clocks")
    page.wait_for_url(f"{base}/events/*/")
    assert "DRILL E-0003" in page.inner_text("main")
    assert "DRILL E-0003" in page.inner_text("#clock-strip")
    assert page.title().startswith("(")  # tab title shows the next deadline
    assert not h_scroll(page)

    page.click("summary:has-text('Early warning filing time')")
    filed = aw + timedelta(minutes=30)
    page.fill("#id_early_warning-when_date", filed.strftime("%Y-%m-%d"))
    page.fill("#id_early_warning-when_time", filed.strftime("%H:%M"))
    page.select_option("#id_early_warning-when_tz", "UTC")
    page.locator("details:has(#id_early_warning-when_date) button").click()
    page.wait_for_load_state("networkidle")
    assert "Time recorded." in page.inner_text("main")
    assert "met" in page.inner_text("table.cards")

    page.check("input[name=outcome][value=closed_not_reportable]")
    page.fill("#id_rationale", "Drill closed: treated as not exploited.")
    page.click("button:has-text('Close event')")
    page.wait_for_load_state("networkidle")
    assert "Closed – determined not reportable" in page.inner_text("main")
    assert "DRILL E-0003" not in page.inner_text("#clock-strip")
    assert not h_scroll(page)
    assert errors == [], (errors, missing)  # includes CSP violations
    ctx.close()
