"""Write audit entries. Always stores the real actor (D9); never updates or deletes."""
from __future__ import annotations

import json
from datetime import date, datetime
from uuid import UUID

from .models import AuditEvent


def _jsonable(value):
    if value is None:
        return None
    return json.loads(json.dumps(value, default=_default))


def _default(o):
    if isinstance(o, datetime):
        return o.isoformat().replace("+00:00", "Z")
    if isinstance(o, date):
        return o.isoformat()
    if isinstance(o, UUID):
        return str(o)
    return str(o)


def actor_role_for(ctx) -> str:
    if ctx is None:
        return "system"
    if ctx.workspace == "customer":
        return "customer_admin"
    return "responder" if ctx.is_responder else "vendor_admin"


def record(request, *, area: str, action: str, target=None, target_label: str = "",
           old=None, new=None, reason: str = "", incident_detail: bool = False,
           drill: bool = False, import_id=None, export_id=None, shared_as: str = "") -> AuditEvent:
    ctx = request.tenant_ctx
    user = request.user
    return AuditEvent.objects.create(
        vendor_tenant_id=ctx.vendor_tenant_id,
        actor_id=user.pk, actor_tenant_id=ctx.tenant_id, actor_name=user.display_name,
        actor_role=actor_role_for(ctx), shared_as=shared_as,
        area=area, action=action,
        target_type=type(target).__name__ if target is not None else "",
        target_id=str(getattr(target, "pk", "") or ""), target_label=target_label,
        old_value=_jsonable(old), new_value=_jsonable(new), reason=reason,
        is_incident_detail=incident_detail, is_drill=drill, import_id=import_id, export_id=export_id,
    )
