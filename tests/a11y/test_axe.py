"""axe-core (WCAG 2.0/2.1/2.2 A and AA) and 320 px reflow on every vendor screen,
at 320 px and 1280 px (technical plan, "Accessibility"; QA-04, QA-05, QA-10)."""
import psycopg
import pytest

pytest.importorskip("axe_playwright_python", reason="axe/Playwright not installed (uv sync --group browser)")

from tests.browser_support import h_scroll, sign_in

pytestmark = [pytest.mark.postgres, pytest.mark.browser]
TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]


def pages(db_url):
    with psycopg.connect(db_url) as c:
        acme = c.execute("SELECT id FROM tenant WHERE legal_name LIKE 'Acme%%'").fetchone()[0]
        one = lambda sql: c.execute(sql, [acme]).fetchone()[0]  # noqa: E731
        ev = one("SELECT id FROM art14_event WHERE vendor_tenant_id=%s AND NOT is_drill")
        rs = one("SELECT id FROM requirement_status WHERE vendor_tenant_id=%s LIMIT 1")
        risk = one("SELECT id FROM ai_risk WHERE vendor_tenant_id=%s LIMIT 1")
    return {"S-2": "/", "S-3": "/requirements/", "S-4": f"/requirements/{rs}/", "S-5": "/ai-risks/",
            "S-6": f"/ai-risks/{risk}/", "S-7": "/events/", "S-8": "/events/log?drill=1", "S-8a": "/events/start",
            "S-9": f"/events/{ev}/", "S-9 details": f"/events/{ev}/details", "S-11": f"/events/{ev}/awareness",
            "S-14": "/setup/", "S-14 users": "/setup/users/", "S-16": "/audit/", "profile": "/profile/",
            "help": "/help/"}


@pytest.fixture(scope="module", params=[320, 1280], ids=lambda w: f"{w}px")
def page(request, browser, live_app):  # noqa: F811
    ctx = browser.new_context(viewport={"width": request.param, "height": 900})
    pg = ctx.new_page()
    sign_in(pg, live_app["url"])
    yield pg
    ctx.close()


@pytest.fixture(scope="module")
def page_map(live_app):  # noqa: F811
    return pages(live_app["db_url"])


SCREENS = ["S-2", "S-3", "S-4", "S-5", "S-6", "S-7", "S-8", "S-8a", "S-9", "S-9 details", "S-11", "S-14",
           "S-14 users", "S-16", "profile", "help"]


@pytest.mark.parametrize("screen", SCREENS)
def test_axe_and_reflow(page, page_map, live_app, screen):  # noqa: F811
    from axe_playwright_python.sync_playwright import Axe
    page.goto(live_app["url"] + page_map[screen])
    page.wait_for_load_state("networkidle")
    # open every disclosure so hidden controls are checked too
    page.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
    res = Axe().run(page, options={"runOnly": {"type": "tag", "values": TAGS}})
    violations = [(v["id"], v["impact"], len(v["nodes"])) for v in res.response["violations"]]
    assert violations == []
    assert not h_scroll(page), "page scrolls sideways"
