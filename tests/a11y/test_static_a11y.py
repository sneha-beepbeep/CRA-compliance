"""Static accessibility checks on every rendered vendor page (WCAG 2.2 AA subset).

Not a substitute for the planned Playwright + axe-core run (tests/a11y/test_axe.py)
or the manual NVDA/VoiceOver pass; it catches the regressions that don't need a browser.
"""
from html.parser import HTMLParser

import pytest
from django.test import Client

from tests.authz_matrix.test_route_matrix import own_id, url
from tests.routes import all_routes

pytestmark = [pytest.mark.postgres, pytest.mark.django_db]


class Audit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lang = None
        self.title = ""
        self.in_title = False
        self.h1 = 0
        self.labels_for = set()
        self.label_depth = 0
        self.inputs = []  # (id, has_aria, inside_label)
        self.th_without_scope = 0
        self.in_thead = False
        self.buttons = []
        self.in_button = False
        self.btn_text = ""
        self.imgs_without_alt = 0
        self.fieldset_inputs = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.h1 += 1
        elif tag == "label":
            self.label_depth += 1
            if a.get("for"):
                self.labels_for.add(a["for"])
        elif tag in ("input", "select", "textarea") and a.get("type") not in ("hidden", "submit"):
            self.inputs.append((a.get("id"), bool(a.get("aria-label") or a.get("aria-labelledby")), self.label_depth > 0))
        elif tag == "th" and "scope" not in a:
            self.th_without_scope += 1
        elif tag == "button":
            self.in_button, self.btn_text = True, ""
        elif tag == "img" and "alt" not in a:
            self.imgs_without_alt += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "label":
            self.label_depth -= 1
        elif tag == "button":
            self.buttons.append(self.btn_text.strip())
            self.in_button = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_button:
            self.btn_text += data


# Every GET page per role (POST-only actions and the strip fragment excluded).
COMMON = ["", "help/", "profile/", "requirements/", "requirements/<uuid:pk>/", "ai-risks/", "ai-risks/<uuid:pk>/",
          "events/", "events/start", "events/<uuid:pk>/", "events/<uuid:pk>/reassign", "setup/", "setup/users/",
          "audit/"]
RESPONDER_ONLY = ["events/log", "events/<uuid:pk>/details", "events/<uuid:pk>/awareness"]
CASES = [(p, "manager") for p in COMMON + RESPONDER_ONLY] + [(p, "admin") for p in COMMON]


def test_case_list_covers_every_get_page():
    routed = {p for p, cb in all_routes()}
    assert set(COMMON + RESPONDER_ONLY) <= routed


@pytest.mark.parametrize("path,who", CASES)
def test_page_basics(world, path, who):
    a = world["A"]
    c = Client()
    c.force_login(getattr(a, who))
    pk = own_id(path, a) if "<uuid:pk>" in path else None
    r = c.get(url(path, pk) if pk else "/" + path)
    assert r.status_code == 200
    p = Audit()
    p.feed(r.content.decode())
    assert p.lang == "en"
    assert p.title.strip()
    assert p.h1 == 1, f"{p.h1} h1 elements"
    unlabelled = [i for i, aria, inside in p.inputs if not aria and not inside and i not in p.labels_for]
    assert unlabelled == [], f"inputs without a label: {unlabelled}"
    assert p.th_without_scope == 0
    assert all(p.buttons), "button without text"
    assert p.imgs_without_alt == 0
