"""Test settings. Postgres-backed tests need DATABASE_URL; without it they skip."""
from .base import *  # noqa: F401,F403
from .base import DATABASES

SECRET_KEY = "test-only-not-secret"  # nosec B105 - test settings only
DEBUG = False
ALLOWED_HOSTS = ["testserver"]
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
if not DATABASES["default"]:
    # Placeholder so Django can import; tests that touch it are skipped.
    DATABASES["default"] = {"ENGINE": "django.db.backends.postgresql", "NAME": "unavailable"}
