"""S-2 vendor overview, help, and the static not-found page."""
from django.http import HttpResponseNotFound
from django.shortcuts import render
from django.template.loader import render_to_string

from apps.airisks.models import AIRisk
from apps.airisks.services import summary as risk_summary
from apps.authz.capabilities import Capability, requires
from apps.registry.services import setup_checklist
from apps.requirements.models import RequirementStatus
from apps.requirements.services import summary as req_summary

from .context_processors import current_version


@requires(Capability.AUTHENTICATED)
def home(request):
    if request.tenant_ctx.workspace == "customer":
        # Customer workspace (S-B0..S-B7) is phase 1b; bank access is gated on the
        # pentest and legal sign-off (C6). Nothing vendor-side is reachable from here.
        return render(request, "customer/not_yet.html")
    version = current_version(request)
    statuses = list(RequirementStatus.objects.filter(version=version).select_related("requirement")) if version else []
    risks = list(AIRisk.objects.filter(version=version)) if version else []
    stale = [s for s in statuses if s.display_status == "evidence_stale"] + \
            [r for r in risks if r.display_stage == "evidence_stale"]
    checklist = setup_checklist(request)
    return render(request, "ui/overview.html", {
        "version": version, "req": req_summary(statuses), "risk": risk_summary(risks), "stale": stale,
        "checklist": checklist})


@requires(Capability.AUTHENTICATED)
def help_page(request):
    return render(request, "ui/help.html")


def not_found(request, exception=None):
    """Identical bytes for 'doesn't exist' and 'not yours' (design 11.3): no
    request-dependent content, no shell, no CSRF token."""
    return HttpResponseNotFound(render_to_string("404.html"))
