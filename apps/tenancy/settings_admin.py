"""Operator changes to global system settings (QA-03; technical plan: "Changes
are audited and need no release").

Settings are global, but the audit trail is per vendor tenant, so every change
is written into every vendor tenant's audit trail (each vendor can see that,
say, real incident data was enabled or the disclaimer changed). The operator's
name and a reason are required.
"""
from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from apps.audit.models import AuditEvent

from .models import SystemSetting, Tenant

REASON_MIN = 20


class SettingError(ValueError):
    pass


def _bool(raw: str) -> bool:
    v = raw.strip().lower()
    if v in ("true", "on", "yes", "1"):
        return True
    if v in ("false", "off", "no", "0"):
        return False
    raise SettingError("Use true or false.")


def _disclaimer(raw: str) -> str:
    raw = raw.strip()
    if "{vendor_legal_name}" not in raw:
        raise SettingError("The disclaimer must contain {vendor_legal_name}.")
    try:
        raw.format(vendor_legal_name="X")
    except (KeyError, IndexError, ValueError):
        raise SettingError("The disclaimer may only use the {vendor_legal_name} placeholder.") from None
    return raw


def _month_rule(raw: str) -> str:
    if raw not in ("calendar_clamp_utc", "days_30"):
        raise SettingError("month_rule must be calendar_clamp_utc or days_30.")
    return raw


def _text(raw: str) -> str:
    if not raw.strip():
        raise SettingError("Value can't be empty.")
    return raw.strip()


@dataclass(frozen=True)
class Spec:
    parse: object
    help: str


SETTINGS = {
    "real_events_enabled": Spec(_bool, "C6 gate: allow real (non-drill) Art. 14 events. true/false."),
    "disclaimer_template": Spec(_disclaimer, "NFR-8 notice; must contain {vendor_legal_name}."),
    "month_rule": Spec(_month_rule, "One-month rule for severe-incident final reports (D10)."),
    "month_rule_note": Spec(_text, "Note shown next to the one-month final report."),
}


def current(key: str):
    return SystemSetting.get(key)


@transaction.atomic
def set_setting(key: str, raw: str, *, operator: str, reason: str) -> tuple[object, object, int]:
    """Validate, store and audit. Returns (old, new, number of vendor audit entries)."""
    if key not in SETTINGS:
        raise SettingError(f"Unknown setting {key!r}. Known: {', '.join(sorted(SETTINGS))}.")
    if not operator.strip():
        raise SettingError("Give the operator's name (--operator).")
    if len(reason.strip()) < REASON_MIN:
        raise SettingError(f"Give a reason of at least {REASON_MIN} characters (--reason).")
    new = SETTINGS[key].parse(raw)
    old = current(key)
    SystemSetting.objects.update_or_create(key=key, defaults={"value": new})
    vendors = list(Tenant.objects.filter(kind=Tenant.Kind.VENDOR).values_list("id", flat=True))
    for vid in vendors:
        AuditEvent.objects.create(
            vendor_tenant_id=vid, actor=None, actor_tenant=None, actor_name=f"Operator: {operator.strip()}",
            actor_role="system", area="system", action="changed_system_setting", target_type="SystemSetting",
            target_id=key, target_label=key, old_value={key: old}, new_value={key: new}, reason=reason.strip())
    return old, new, len(vendors)
