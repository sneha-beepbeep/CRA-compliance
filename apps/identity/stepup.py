"""Step-up re-authentication for "Mark informed" (D6; screen S-10 is phase 1b).

A fresh MFA authentication (`auth_time` no more than 5 minutes old) grants one
single-use token bound to one action and one object.
"""
import secrets
import time

from django.conf import settings


def is_fresh(request, now: float | None = None) -> bool:
    auth_time = request.session.get("auth_time")
    now = now if now is not None else time.time()
    return auth_time is not None and now - auth_time <= settings.STEP_UP_MAX_AGE_SECONDS


def issue_token(request, action: str, object_id: str, now: float | None = None) -> str | None:
    if not is_fresh(request, now):
        return None
    token = secrets.token_urlsafe(24)
    request.session[f"stepup:{token}"] = {"action": action, "object": str(object_id)}
    return token


def consume_token(request, token: str, action: str, object_id: str, now: float | None = None) -> bool:
    """Valid once, for the named action and object, while auth_time is still fresh."""
    data = request.session.pop(f"stepup:{token}", None)
    return bool(data) and data == {"action": action, "object": str(object_id)} and is_fresh(request, now)
