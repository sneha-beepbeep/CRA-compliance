"""Option D in a real browser: the one-time time-zone banner.

* JS on: the browser's IANA zone (Intl) is pre-selected; axe-clean and no
  sideways scroll at 1280 px and 320 px; confirming hides the banner for good.
* JS off: the banner still works as a plain form with a manual choice.
"""
import pytest

pytest.importorskip("axe_playwright_python", reason="axe/Playwright not installed (uv sync --group browser)")
from axe_playwright_python.sync_playwright import Axe  # noqa: E402

from tests.browser_support import h_scroll, sign_in  # noqa: E402

pytestmark = [pytest.mark.postgres, pytest.mark.browser]
TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]


def axe_violations(page):
    res = Axe().run(page, options={"runOnly": {"type": "tag", "values": TAGS}})
    return [(v["id"], v["impact"], len(v["nodes"])) for v in res.response["violations"]]


def test_banner_detects_zone_and_confirms(browser, live_app):
    base = live_app["url"]
    for width in (1280, 320):
        ctx = browser.new_context(viewport={"width": width, "height": 900}, timezone_id="Europe/Warsaw")
        page = ctx.new_page()
        sign_in(page, base, "admin@acme.example")
        page.goto(base + "/requirements/")
        banner = page.locator("#tz-banner")
        assert banner.is_visible()
        assert page.locator("#tz-banner select").input_value() == "Europe/Warsaw"
        assert page.locator("#tz-detected-name").inner_text() == "Europe/Warsaw"
        assert page.locator("#tz-banner input[name=detected]").input_value() == "Europe/Warsaw"
        assert axe_violations(page) == []
        assert not h_scroll(page)
        if width == 320:
            page.click("#tz-banner button")
            page.wait_for_url(base + "/requirements/")
            assert page.locator("#tz-banner").count() == 0
            assert "Times shown: Europe/Warsaw" in page.inner_text("footer")
            page.goto(base + "/")
            assert page.locator("#tz-banner").count() == 0  # one-time
        ctx.close()


def test_banner_works_without_javascript(browser, live_app):
    base = live_app["url"]
    ctx = browser.new_context(java_script_enabled=False, viewport={"width": 320, "height": 900},
                              timezone_id="Asia/Tokyo")
    page = ctx.new_page()
    sign_in(page, base, "admin@other.example")
    assert page.locator("#tz-banner select").input_value() == "UTC"  # nothing detected without JS
    assert page.locator("#tz-detected").is_hidden()
    page.select_option("#tz-banner select", "Europe/Dublin")
    page.click("#tz-banner button")
    page.wait_for_load_state()
    assert page.locator("#tz-banner").count() == 0
    assert "Times shown: Europe/Dublin" in page.inner_text("footer")
    ctx.close()
