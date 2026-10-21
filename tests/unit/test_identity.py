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
