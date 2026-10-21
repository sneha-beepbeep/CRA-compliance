"""S-16 audit trail: masked for non-responders, customer actors per D9."""
from datetime import datetime, time, timezone

from django.shortcuts import render

from apps.authz.capabilities import Capability, requires
from apps.tenancy.models import ActivitySharingSetting, Tenant

from .models import AuditEvent
from .render import action_label
from .render import render as render_entry

PAGE = 200


@requires(Capability.AUDIT_VIEW)
def audit_list(request):
    qs = AuditEvent.objects.all().order_by("-seq")
    area, action, ref = request.GET.get("area", ""), request.GET.get("action", ""), request.GET.get("ref", "").strip()
    if area:
        qs = qs.filter(area=area)
    if action:
        qs = qs.filter(action=action)
    if ref:
        qs = qs.filter(target_label__icontains=ref)
    for key, op in (("from", "gte"), ("to", "lte")):
        val = request.GET.get(key, "")
        if val:
            try:
                d = datetime.strptime(val, "%Y-%m-%d").date()
            except ValueError:
                continue
            t = time.min if op == "gte" else time.max
            qs = qs.filter(**{f"created_at__{op}": datetime.combine(d, t, tzinfo=timezone.utc)})
    modes = {str(s.customer_tenant_id): s.mode for s in ActivitySharingSetting.objects.all()}
    names = {str(t.pk): t.display_name for t in Tenant.objects.filter(kind="customer")}
    tz = request.user.time_zone
    entries = [render_entry(e, request.tenant_ctx, current_modes=modes, customer_names=names, tz=tz)
               for e in qs[:PAGE]]
    return render(request, "audit/list.html", {
        "entries": entries, "areas": sorted(set(AuditEvent.objects.values_list("area", flat=True))),
        "actions": sorted({(a, action_label(a)) for a in AuditEvent.objects.values_list("action", flat=True)},
                          key=lambda x: x[1]),
        "f": request.GET, "truncated": qs.count() > PAGE})
