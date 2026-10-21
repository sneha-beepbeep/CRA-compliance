"""Shared settings. Environment-specific values live in dev.py / prod.py / test.py."""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def database_from_url(url: str | None) -> dict:
    """Minimal DATABASE_URL parser (postgres://user:pass@host:port/name?host=/socket/dir)."""
    if not url:
        return {}
    p = urlparse(url)
    if p.scheme not in ("postgres", "postgresql"):
        raise ValueError("Only PostgreSQL is supported (row-level security is required).")
    query = dict(q.split("=", 1) for q in p.query.split("&") if "=" in q)
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(p.path.lstrip("/")),
        "USER": unquote(p.username or ""),
        "PASSWORD": unquote(p.password or ""),
        "HOST": unquote(query.get("host", p.hostname or "")),
        "PORT": str(p.port or ""),
        # The tenant context middleware wraps each request in its own transaction
        # (SET LOCAL ROLE / set_config(..., true) are transaction-scoped).
        "ATOMIC_REQUESTS": False,
        "CONN_MAX_AGE": 0,
        "TEST": {"NAME": unquote(p.path.lstrip("/")) + "_test"},
    }


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
DEBUG = False
ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    # No django.contrib.admin: leaving it out enforces "no support-staff access
    # to tenant data" (technical plan, Architecture).
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "apps.tenancy",
    "apps.identity",
    "apps.authz",
    "apps.audit",
    "apps.catalog",
    "apps.registry",
    "apps.requirements",
    "apps.airisks",
    "apps.art14",
    "apps.release",
    "apps.customer",
    "apps.imports",
    "apps.exports",
    "apps.ui",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.identity.middleware.SessionLimitsMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "apps.ui.middleware.SecurityHeadersMiddleware",
    # Must be last: wraps the view in a transaction with the tenant context and
    # the database role (app_vendor / app_customer) set.
    "apps.tenancy.middleware.TenantContextMiddleware",
]

ROOT_URLCONF = "tracker.urls"
WSGI_APPLICATION = "tracker.wsgi.application"
AUTH_USER_MODEL = "tenancy.UserAccount"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.ui.context_processors.shell",
            ],
        },
    },
]

DATABASES = {"default": database_from_url(os.environ.get("DATABASE_URL"))}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

USE_TZ = True
TIME_ZONE = "UTC"  # storage and server clock are UTC (NFR-4)
LANGUAGE_CODE = "en-gb"
USE_I18N = False

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# --- Sessions (design 11.6, D6) ------------------------------------------------
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_LIMITS = {
    "vendor": {"idle_seconds": 8 * 3600, "absolute_seconds": 24 * 3600},
    "customer": {"idle_seconds": 30 * 60, "absolute_seconds": 8 * 3600},
}
STEP_UP_MAX_AGE_SECONDS = 5 * 60
# Requests that must not reset the idle timer (clock-strip polling).
SESSION_PASSIVE_PATHS = ("/clocks/strip",)

# --- Identity: Keycloak over OIDC (mozilla-django-oidc) -------------------------
AUTHENTICATION_BACKENDS = ["apps.identity.oidc.TrackerOIDCBackend"]
OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID", "tracker")
OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET", "")
OIDC_RP_SIGN_ALGO = "RS256"
_KC = os.environ.get("KEYCLOAK_REALM_URL", "http://localhost:8080/realms/tracker")
OIDC_OP_AUTHORIZATION_ENDPOINT = f"{_KC}/protocol/openid-connect/auth"
OIDC_OP_TOKEN_ENDPOINT = f"{_KC}/protocol/openid-connect/token"
OIDC_OP_USER_ENDPOINT = f"{_KC}/protocol/openid-connect/userinfo"
OIDC_OP_JWKS_ENDPOINT = f"{_KC}/protocol/openid-connect/certs"
OIDC_OP_LOGOUT_ENDPOINT = f"{_KC}/protocol/openid-connect/logout"
OIDC_RP_SCOPES = "openid email profile"
OIDC_CREATE_USER = False  # users are provisioned or invited, never self-created
OIDC_STORE_ID_TOKEN = False
LOGIN_URL = "/sign-in/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/signed-out/"
# Development-only shortcut sign-in; never enabled in prod.py (tested).
DEV_LOGIN_ENABLED = False

# --- Security headers -----------------------------------------------------------
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    # No incident text or personal data in logs: request bodies are never logged.
    "root": {"handlers": ["console"], "level": "INFO"},
}

STATICFILES_DIRS = [BASE_DIR / "static"]

# Feature flags. Customer invitations arrive in phase 1b; until then the optional
# "Invite a customer admin" setup step is hidden (deviation 13).
CUSTOMER_INVITATIONS_ENABLED = False
