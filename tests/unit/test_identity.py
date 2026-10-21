"""Step-up (D6), session limits (11.6) and the dev-login guard."""
import importlib
import time
from types import SimpleNamespace as NS

import pytest
from django.test import RequestFactory, override_settings

from apps.identity import stepup
from apps.identity.middleware import SessionLimitsMiddleware
from apps.identity.oidc import MFA_AMR, TrackerOIDCBackend


class Session(dict):
    pass


def req(auth_time=None):
    r = NS(session=Session())
    if auth_time is not None:
        r.session["auth_time"] = auth_time
    return r


def test_step_up_fresh_within_5_minutes():
    now = 1_000_000.0
    assert stepup.is_fresh(req(now - 300), now)
    assert not stepup.is_fresh(req(now - 301), now)
    assert not stepup.is_fresh(req(), now)


def test_step_up_token_single_use_and_bound():
    now = 1_000_000.0
    r = req(now - 10)
    tok = stepup.issue_token(r, "mark_informed", "ev1", now)
    assert tok and not stepup.consume_token(r, tok, "mark_informed", "ev2", now)  # wrong object, burnt
    tok = stepup.issue_token(r, "mark_informed", "ev1", now)
    assert stepup.consume_token(r, tok, "mark_informed", "ev1", now)
    assert not stepup.consume_token(r, tok, "mark_informed", "ev1", now)  # single use


def test_step_up_refused_when_stale():
    assert stepup.issue_token(req(0), "mark_informed", "ev1", 10_000) is None


def user(kind):
    return NS(is_authenticated=True, tenant=NS(kind=kind))


def run(kind, path, session, monkeypatch, now):
    monkeypatch.setattr(time, "time", lambda: now)
    calls = []
    mw = SessionLimitsMiddleware(lambda r: calls.append(r) or "ok")
    r = RequestFactory().get(path)
    r.user = user(kind)
    r.session = session
    monkeypatch.setattr("apps.identity.middleware.logout", lambda req: req.session.clear())
    return mw(r), session


@pytest.mark.parametrize("kind,idle", [("vendor", 8 * 3600), ("customer", 30 * 60)])
def test_idle_timeout(kind, idle, monkeypatch):
    s = Session(session_started=0, last_activity=0)
    out, _ = run(kind, "/", s, monkeypatch, idle)
    assert out == "ok"
    s = Session(session_started=0, last_activity=0)
    out, _ = run(kind, "/", s, monkeypatch, idle + 1)
    assert out.status_code == 302 and "expired" in out["Location"]


@pytest.mark.parametrize("kind,absolute", [("vendor", 24 * 3600), ("customer", 8 * 3600)])
def test_absolute_limit(kind, absolute, monkeypatch):
    s = Session(session_started=0, last_activity=absolute)
    out, _ = run(kind, "/", s, monkeypatch, absolute + 1)
    assert out.status_code == 302


def test_strip_polling_does_not_reset_idle(monkeypatch):
    s = Session(session_started=0, last_activity=100)
    run("vendor", "/clocks/strip", s, monkeypatch, 200)
    assert s["last_activity"] == 100
    run("vendor", "/requirements/", s, monkeypatch, 300)
    assert s["last_activity"] == 300


def test_oidc_requires_mfa_amr():
    b = TrackerOIDCBackend.__new__(TrackerOIDCBackend)
    b.request = None
    assert b.get_or_create_user("a", "i", {"sub": "x", "amr": ["pwd"]}) is None
    assert {"otp", "webauthn"} <= MFA_AMR


def test_prod_settings_disable_dev_login(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "x" * 50)
    prod = importlib.import_module("tracker.settings.prod")
    assert prod.DEV_LOGIN_ENABLED is False and prod.DEBUG is False
    assert prod.SESSION_COOKIE_SECURE and prod.CSRF_COOKIE_SECURE and prod.SECURE_HSTS_SECONDS > 0
    assert "django.contrib.admin" not in prod.INSTALLED_APPS
    assert "django.contrib.auth.backends.ModelBackend" not in prod.AUTHENTICATION_BACKENDS


def test_dev_login_not_routed_without_flag():
    from django.urls import Resolver404, resolve
    with pytest.raises(Resolver404):
        resolve("/dev/login/")


# QA-11: S-0 sign-in error states
class _Req:
    def __init__(self):
        self.session = {}


def test_mfa_refusal_is_explained():
    b = TrackerOIDCBackend.__new__(TrackerOIDCBackend)
    b.request = _Req()
    assert b.get_or_create_user("a", "i", {"sub": "x", "amr": ["pwd"]}) is None
    assert b.request.session["signin_error"] == "mfa"


def test_failure_redirect_lands_on_sign_in():
    from django.conf import settings
    assert settings.LOGIN_REDIRECT_URL_FAILURE == "/sign-in/?error=1"


@pytest.mark.parametrize("reason,text", [("mfa", "authenticator app or a passkey"),
                                         ("no_account", "You don't have access to this workspace."),
                                         ("failed", "Sign-in didn't complete. Contact your administrator.")])
def test_sign_in_page_messages(reason, text):
    from django.contrib.auth.models import AnonymousUser
    from django.contrib.sessions.backends.signed_cookies import SessionStore

    from apps.identity.views import sign_in
    r = RequestFactory().get("/sign-in/?error=1" if reason == "failed" else "/sign-in/")
    r.user, r.session, r.tenant_ctx = AnonymousUser(), SessionStore(), None
    if reason != "failed":
        r.session["signin_error"] = reason
    body = sign_in(r).content.decode()
    assert text in body.replace("&#x27;", "'")
    assert "signin_error" not in r.session  # shown once


# Option D: server-side zone validation and the no-network banner script
def test_valid_zone_against_iana_list():
    from apps.tenancy.services import valid_zone
    assert valid_zone("Europe/Warsaw") == "Europe/Warsaw" and valid_zone("UTC") == "UTC"
    for bad in (None, "", "Mars/Olympus", "../etc/passwd", "europe/warsaw"):
        assert valid_zone(bad) is None


def test_banner_form_choices_are_iana():
    from zoneinfo import available_timezones

    from apps.tenancy.views import ConfirmTimeZoneForm
    choices = {v for v, _ in ConfirmTimeZoneForm().fields["time_zone"].choices}
    assert "UTC" in choices and "Europe/Warsaw" in choices and choices <= available_timezones()


def test_timezone_js_makes_no_requests_and_uses_intl():
    from pathlib import Path
    js = (Path(__file__).resolve().parents[2] / "static" / "js" / "timezone.js").read_text()
    assert "Intl.DateTimeFormat().resolvedOptions().timeZone" in js
    for forbidden in ("fetch(", "XMLHttpRequest", "htmx", "eval(", "submit()"):
        assert forbidden not in js
