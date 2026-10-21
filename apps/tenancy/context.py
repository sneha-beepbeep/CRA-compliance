"""Per-request tenant context: who is calling, from which tenant, with which role.

Resolved fresh on every request (the responder role is never cached in the session).
"""
from __future__ import annotations

from dataclasses import dataclass

from django.db import connection


@dataclass(frozen=True)
class TenantContext:
    user_id: str
    tenant_id: str
    vendor_tenant_id: str
    workspace: str  # "vendor" | "customer"
    is_responder: bool
    is_access_manager: bool

    @property
    def roles(self) -> frozenset[str]:
        if self.workspace == "customer":
            return frozenset({"customer_admin"})
        r = {"vendor_admin"}
        if self.is_responder:
            r.add("incident_responder")
        if self.is_access_manager:
            r.add("access_manager")
        return frozenset(r)


def resolve(user) -> TenantContext | None:
    """Build the context with the login role's own rights (before SET ROLE)."""
    if user is None or not getattr(user, "is_authenticated", False) or not user.is_active:
        return None
    from apps.tenancy.models import RoleGrant, Tenant

    tenant = Tenant.objects.only("id", "kind", "vendor_tenant_id").get(pk=user.tenant_id)
    responder = (tenant.kind == Tenant.Kind.VENDOR and RoleGrant.objects.filter(
        user_id=user.pk, role=RoleGrant.Role.INCIDENT_RESPONDER, revoked_at__isnull=True).exists())
    return TenantContext(
        user_id=str(user.pk), tenant_id=str(tenant.id), vendor_tenant_id=str(tenant.vendor_tenant_id),
        workspace="vendor" if tenant.kind == Tenant.Kind.VENDOR else "customer",
        is_responder=responder, is_access_manager=bool(user.is_access_manager and tenant.kind == "vendor"))


def apply(ctx: TenantContext | None, conn=None) -> None:
    """Set the database role and GUCs for the current transaction (SET LOCAL semantics)."""
    conn = conn or connection
    with conn.cursor() as cur:
        if ctx is None:
            # Anonymous: run as the vendor role with no tenant -> 0 rows everywhere.
            cur.execute("SELECT set_config('app.tenant_id', '', true), set_config('app.is_responder', '', true),"
                        " set_config('app.vendor_tenant_id', '', true)")
            cur.execute("SET LOCAL ROLE app_vendor")
            return
        cur.execute("SELECT set_config('app.tenant_id', %s, true), set_config('app.is_responder', %s, true),"
                    " set_config('app.vendor_tenant_id', %s, true)",
                    [ctx.tenant_id, "on" if ctx.is_responder else "", ctx.vendor_tenant_id])
        cur.execute("SET LOCAL ROLE app_vendor" if ctx.workspace == "vendor" else "SET LOCAL ROLE app_customer")


def reset(conn=None) -> None:
    conn = conn or connection
    with conn.cursor() as cur:
        cur.execute("RESET ROLE")
        cur.execute("SELECT set_config('app.tenant_id', '', true), set_config('app.is_responder', '', true),"
                    " set_config('app.vendor_tenant_id', '', true)")
