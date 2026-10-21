"""S-0 sign-in and access states."""
from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.authz.capabilities import Capability, requires

from .oidc import record_auth_time


@requires(Capability.PUBLIC, db_context_exempt=True)
def sign_in(request):
    if request.user.is_authenticated:
        return redirect("/")
    return render(request, "identity/sign_in.html", {"dev_login": settings.DEV_LOGIN_ENABLED})


@requires(Capability.PUBLIC, db_context_exempt=True)
def signed_out(request):
    return render(request, "identity/signed_out.html", {"expired": request.GET.get("reason") == "expired"})


@requires(Capability.PUBLIC, db_context_exempt=True)
@require_http_methods(["POST"])
def sign_out(request):
    logout(request)
    return redirect("/signed-out/")


@requires(Capability.PUBLIC, db_context_exempt=True)
@require_http_methods(["GET", "POST"])
def dev_login(request):
    """Development only: sign in as a seeded user without Keycloak.

    Not routed unless DEV_LOGIN_ENABLED (dev.py only); a test asserts prod.py keeps it off.
    """
    if not settings.DEV_LOGIN_ENABLED:
        raise Http404
    User = get_user_model()
    users = User.objects.filter(is_active=True).select_related("tenant").order_by("tenant__display_name", "email")
    if request.method == "POST":
        user = users.filter(email=request.POST.get("email", "")).first()
        if user is None:
            return render(request, "identity/dev_login.html", {"users": users, "error": True}, status=400)
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        record_auth_time(request)
        return redirect("/")
    return render(request, "identity/dev_login.html", {"users": users})
