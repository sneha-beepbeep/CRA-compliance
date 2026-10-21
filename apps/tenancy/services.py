"""Role management (access managers only, D5)."""
from django.db import transaction

from apps.audit.log import record
from apps.core import clock

from .models import RoleGrant, UserAccount


@transaction.atomic
def grant_responder(request, user: UserAccount):
    if user.tenant_id != request.user.tenant_id:
        raise ValueError("not in this tenant")
    if RoleGrant.objects.filter(user=user, role=RoleGrant.Role.INCIDENT_RESPONDER, revoked_at__isnull=True).exists():
        return
    RoleGrant.objects.create(vendor_tenant_id=user.vendor_tenant_id, user=user,
                             role=RoleGrant.Role.INCIDENT_RESPONDER, granted_by=request.user, granted_at=clock.now())
    record(request, area="users", action="granted_responder", target=user, target_label=user.display_name)


@transaction.atomic
def revoke_responder(request, user: UserAccount):
    n = RoleGrant.objects.filter(user=user, role=RoleGrant.Role.INCIDENT_RESPONDER, revoked_at__isnull=True).update(
        revoked_at=clock.now(), revoked_by=request.user)
    if n:
        record(request, area="users", action="revoked_responder", target=user, target_label=user.display_name)


@transaction.atomic
def set_time_zone(request, tz_name: str):
    from apps.art14.localtime import get_zone
    get_zone(tz_name)
    old = request.user.time_zone
    UserAccount.objects.filter(pk=request.user.pk).update(time_zone=tz_name, time_zone_confirmed=True)
    record(request, area="users", action="set_time_zone", target=request.user, target_label=request.user.display_name,
           old={"time_zone": old}, new={"time_zone": tz_name})
