"""Render audit entries for a viewer (design 13, 9.6).

* Incident-detail values are masked for vendor admins without the responder
  role, except in the starter's own "Started clock" entry.
* Customer actors are shown by name only when the entry was recorded under
  "named" AND the customer's current setting is "named" (technical plan, D9):
  named -> organisation-only applies retroactively; organisation-only -> named
  applies forward only.
"""
from __future__ import annotations

from dataclasses import dataclass

import re
from datetime import datetime

MASK = "[value hidden: responders only]"

# QA-08: human-readable actions and values (design 13).
ACTION_LABELS = {
    "started_clock": "Started clock", "logged_event": "Logged event", "viewed_details": "Viewed details",
    "edited_details": "Edited details", "edited_awareness_time": "Edit awareness time",
    "recorded_early_warning": "Recorded early warning filing", "corrected_early_warning": "Corrected early warning filing",
    "recorded_notification": "Recorded notification filing", "corrected_notification": "Corrected notification filing",
    "recorded_final_report": "Recorded final report filing", "corrected_final_report": "Corrected final report filing",
    "recorded_fix": "Recorded fix or mitigation time", "corrected_fix": "Corrected fix or mitigation time",
    "closed_event": "Closed event", "reopened_event": "Reopened event", "reassigned_responder": "Reassigned responder",
    "took_over": "Took over", "recorded_drill_outcome": "Recorded drill outcome",
    "status_change": "Status change", "added_evidence": "Added evidence item", "added_risk": "Added risk",
    "seeded_register": "Seeded register", "stage_change": "Handling stage change", "marked_reviewed": "Marked reviewed",
    "linked_requirement": "Linked requirement", "added_product": "Added product", "added_version": "Added version",
    "added_customer": "Added customer", "added_deployment": "Added deployment",
    "changed_deployment_version": "Changed deployment version", "granted_responder": "Granted incident responder role",
    "revoked_responder": "Removed incident responder role", "set_time_zone": "Set time zone",
    "confirmed_time_zone": "Confirmed time zone",
    "changed_system_setting": "Changed system setting",
}
FIELD_LABELS = {
    "awareness_at": "Awareness time", "early_warning_filed_at": "Early warning filed",
    "notification_filed_at": "Notification filed", "final_report_filed_at": "Final report filed",
    "fix_available_at": "Fix or mitigation available", "review_by": "Review by", "assigned": "Assigned to",
    "early_warning_would_be_met": "Early warning would have been met",
}
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?(\.\d+)?Z$")


def action_label(code: str) -> str:
    return ACTION_LABELS.get(code, code.replace("_", " ").capitalize())


def _value(v, tz):
    from apps.art14.localtime import format_dual
    if isinstance(v, str) and ISO.match(v):
        return format_dual(datetime.fromisoformat(v.replace("Z", "+00:00")), tz)
    if v is None or v == "":
        return "–"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, list):
        return ", ".join(str(x) for x in v) or "–"
    return str(v).replace("_", " ") if isinstance(v, str) and " " not in v and "_" in v else str(v)


def readable(value, tz: str) -> str:
    """'Awareness time: Thu 22 Oct 2026, 08:05 CEST · 06:05 UTC; Reason: …' instead of a dict."""
    if value is None:
        return ""
    if value == MASK:
        return MASK
    if isinstance(value, dict):
        return "; ".join(f"{FIELD_LABELS.get(k, k.replace('_', ' ').capitalize())}: {_value(v, tz)}"
                         for k, v in value.items())
    return _value(value, tz)
ROLE_LABEL = {"vendor_admin": "admin", "responder": "responder", "customer_admin": "customer", "system": "system"}


@dataclass(frozen=True)
class RenderedEntry:
    seq: int
    created_at: object
    who: str
    role: str
    action: str
    target: str
    old: object
    new: object
    reason: str
    masked: bool
    note: str
    action_label: str = ""
    old_text: str = ""
    new_text: str = ""


def actor_display(entry, current_modes: dict, customer_names: dict) -> tuple[str, str]:
    if entry.actor_role != "customer_admin":
        return entry.actor_name, ""
    org = customer_names.get(str(entry.actor_tenant_id), "Customer")
    current = current_modes.get(str(entry.actor_tenant_id), "organisation")
    if entry.shared_as == "named" and current == "named":
        return f"{entry.actor_name} ({org})", ""
    return f"{org} user", f"({org} shares activity as organisation only)"


def render(entry, viewer_ctx, *, current_modes: dict | None = None,
           customer_names: dict | None = None, tz: str = "UTC") -> RenderedEntry:
    who, note = actor_display(entry, current_modes or {}, customer_names or {})
    own_start = entry.action == "started_clock" and str(entry.actor_id) == str(viewer_ctx.user_id)
    masked = entry.is_incident_detail and not viewer_ctx.is_responder and not own_start
    old = MASK if masked and entry.old_value is not None else entry.old_value
    new = MASK if masked and entry.new_value is not None else entry.new_value
    return RenderedEntry(
        seq=entry.seq, created_at=entry.created_at, who=who, role=ROLE_LABEL.get(entry.actor_role, ""),
        action=entry.action, target=entry.target_label, old=old, new=new,
        reason=MASK if masked and entry.reason else entry.reason,
        masked=masked, note=note, action_label=action_label(entry.action),
        old_text=readable(old, tz), new_text=readable(new, tz),
    )
