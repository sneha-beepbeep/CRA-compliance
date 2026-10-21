"""Session limits (design 11.6, D6).

Idle timeout 8 h (vendor) / 30 min (customer); absolute 24 h / 8 h. Clock-strip
polling does not reset the idle timer (technical plan, "Live clock strip").
"""
import time

from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect


def _workspace(user) -> str:
    return "vendor" if user.tenant.kind == "vendor" else "customer"


class SessionLimitsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            now = int(time.time())
            limits = settings.SESSION_LIMITS[_workspace(user)]
            started = request.session.get("session_started", now)
            last = request.session.get("last_activity", now)
            if now - last > limits["idle_seconds"] or now - started > limits["absolute_seconds"]:
                logout(request)
                if request.headers.get("HX-Request"):
                    from django.http import HttpResponse
                    resp = HttpResponse(status=401)
                    resp["HX-Redirect"] = "/signed-out/?reason=expired"
                    return resp
                return redirect("/signed-out/?reason=expired")
            request.session.setdefault("session_started", now)
            if not request.path.startswith(settings.SESSION_PASSIVE_PATHS):
                request.session["last_activity"] = now
            else:
                request.session.setdefault("last_activity", now)
        return self.get_response(request)
