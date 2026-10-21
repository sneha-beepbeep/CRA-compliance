"""Shell context (S-1): disclaimer, product/version selector, clock strip, footer."""
from apps.core import clock
from apps.tenancy.models import SystemSetting

PRODUCT_NAME = "Tracker"  # working title


def disclaimer(vendor_legal_name: str) -> str:
    return SystemSetting.get("disclaimer_template").format(vendor_legal_name=vendor_legal_name)


def tab_title(rows, vendor_name: str) -> str:
    base = f"{PRODUCT_NAME} – {vendor_name}"
    real = [r for r in rows if r.event is not None or r.message]
    if not real:
        return base
    top = real[0]
    if top.tier.value == "overdue":
        return f"(OVERDUE) {base}"
    from apps.art14.deadlines import format_countdown
    from apps.ui.templatetags.tracker import CLOCK_SHORT
    return f"({CLOCK_SHORT[top.next_clock.kind]} {format_countdown(top.next_clock.due_at, clock.now())}) {base}"


def shell(request):
    ctx = getattr(request, "tenant_ctx", None)
    if ctx is None:
        return {"product_name": PRODUCT_NAME}
    from apps.tenancy.models import Tenant
    tenant = Tenant.objects.filter(pk=ctx.tenant_id).first() if ctx.workspace == "vendor" else None
    out = {"product_name": PRODUCT_NAME, "tenant": tenant, "server_now": clock.now(),
           "workspace": ctx.workspace, "roles": ctx.roles}
    if ctx.workspace == "customer":
        from django.db import connection
        with connection.cursor() as cur:  # app_customer can read only the cust_* views
            cur.execute("SELECT vendor_legal_name FROM cust_deployment LIMIT 1")
            row = cur.fetchone()
            cur.execute("SELECT value #>> '{}' FROM cust_system_setting")
            tpl = cur.fetchone()
        template = tpl[0] if tpl else SystemSetting.DEFAULTS["disclaimer_template"]
        out["disclaimer"] = template.format(vendor_legal_name=row[0] if row else "the vendor")
        return out
    if tenant is None:
        return out
    from apps.art14.services import strip_rows
    from apps.registry.models import ProductVersion
    rows = strip_rows(ctx.vendor_tenant_id)
    versions = list(ProductVersion.objects.select_related("product").order_by("product__name", "-created_at"))
    current = current_version(request, versions)
    if not getattr(request.user, "time_zone_confirmed", True):
        from apps.tenancy.views import ConfirmTimeZoneForm
        out["tz_banner_form"] = ConfirmTimeZoneForm(initial={"time_zone": request.user.time_zone,
                                                             "next": request.get_full_path()})
    out.update({
        "disclaimer": disclaimer(tenant.legal_name),
        "strip_rows": rows[:3], "strip_more": max(0, len(rows) - 3),
        "tab_title": tab_title(rows, tenant.display_name),
        "versions": versions, "current_version": current,
    })
    return out


def current_version(request, versions=None):
    from apps.registry.models import ProductVersion
    vid = request.session.get("version_id")
    versions = versions if versions is not None else list(ProductVersion.objects.select_related("product"))
    for v in versions:
        if str(v.pk) == vid:
            return v
    return versions[0] if versions else None
