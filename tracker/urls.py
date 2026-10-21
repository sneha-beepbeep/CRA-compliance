"""Every route declares a capability (apps/authz/capabilities.py); the
route-registry test fails if one doesn't."""
from django.conf import settings
from django.urls import path
from mozilla_django_oidc.views import OIDCAuthenticationCallbackView, OIDCAuthenticationRequestView

from apps.airisks import views as airisks
from apps.art14 import views as art14
from apps.audit import views as audit
from apps.authz.capabilities import Capability, requires
from apps.identity import views as identity
from apps.registry import views as registry
from apps.requirements import views as requirements
from apps.tenancy import views as tenancy
from apps.ui import views as ui

oidc_start = requires(Capability.PUBLIC, db_context_exempt=True)(OIDCAuthenticationRequestView.as_view())
oidc_callback = requires(Capability.PUBLIC, db_context_exempt=True)(OIDCAuthenticationCallbackView.as_view())

urlpatterns = [
    path("", ui.home),
    path("help/", ui.help_page),
    # S-0 sign-in
    path("sign-in/", identity.sign_in),
    path("signed-out/", identity.signed_out),
    path("sign-out/", identity.sign_out),
    path("oidc/authenticate/", oidc_start, name="oidc_authentication_init"),
    path("oidc/callback/", oidc_callback, name="oidc_authentication_callback"),
    path("profile/", tenancy.profile),
    path("profile/time-zone", tenancy.confirm_time_zone),
    # S-1 clock strip partial (polled every 30 s; doesn't reset the idle timer)
    path("clocks/strip", art14.strip),
    # S-3/S-4
    path("requirements/", requirements.requirement_list),
    path("requirements/<uuid:pk>/", requirements.requirement_detail),
    path("requirements/<uuid:pk>/evidence", requirements.add_evidence),
    # S-5/S-6
    path("ai-risks/", airisks.risk_list),
    path("ai-risks/add", airisks.risk_add),
    path("ai-risks/seed", airisks.seed),
    path("ai-risks/<uuid:pk>/", airisks.risk_detail),
    path("ai-risks/<uuid:pk>/evidence", airisks.risk_evidence),
    path("ai-risks/<uuid:pk>/reviewed", airisks.risk_reviewed),
    path("ai-risks/<uuid:pk>/link", airisks.risk_link),
    # S-7..S-13
    path("events/", art14.event_list),
    path("events/log", art14.log_event),
    path("events/start", art14.start_clock),
    path("events/<uuid:pk>/", art14.detail),
    path("events/<uuid:pk>/started/", art14.started),
    path("events/<uuid:pk>/time", art14.record_time),
    path("events/<uuid:pk>/details", art14.edit_details),
    path("events/<uuid:pk>/awareness", art14.edit_awareness),
    path("events/<uuid:pk>/close", art14.close),
    path("events/<uuid:pk>/reopen", art14.reopen),
    path("events/<uuid:pk>/take-over", art14.take_over),
    path("events/<uuid:pk>/reassign", art14.reassign),
    path("events/<uuid:pk>/drill-outcome", art14.drill_outcome),
    # S-14
    path("setup/", registry.setup),
    path("setup/product", registry.add_product),
    path("setup/version", registry.add_version),
    path("setup/deployment", registry.add_deployment),
    path("setup/users/", tenancy.users),
    path("setup/users/<uuid:pk>/responder", tenancy.set_responder),
    path("version/select", registry.select_version),
    # S-16
    path("audit/", audit.audit_list),
]

if settings.DEV_LOGIN_ENABLED:
    urlpatterns.append(path("dev/login/", identity.dev_login))

handler404 = "apps.ui.views.not_found"
