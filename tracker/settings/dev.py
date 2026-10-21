from .base import *  # noqa: F401,F403
from .base import DATABASES

DEBUG = True
SECRET_KEY = SECRET_KEY or "dev-only-not-secret"  # noqa: F405
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
# Lets a developer sign in as a seeded user without Keycloak. Dev only.
DEV_LOGIN_ENABLED = True
AUTHENTICATION_BACKENDS = [
    "apps.identity.oidc.TrackerOIDCBackend",
    "django.contrib.auth.backends.ModelBackend",
]
if not DATABASES["default"]:
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured("Set DATABASE_URL to a PostgreSQL 16 database (scripts/localpg.sh start prints one).")
