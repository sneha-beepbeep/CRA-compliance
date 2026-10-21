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

MASK = "[value hidden: responders only]"
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


def actor_display(entry, current_modes: dict, customer_names: dict) -> tuple[str, str]:
    if entry.actor_role != "customer_admin":
        return entry.actor_name, ""
    org = customer_names.get(str(entry.actor_tenant_id), "Customer")
    current = current_modes.get(str(entry.actor_tenant_id), "organisation")
    if entry.shared_as == "named" and current == "named":
        return f"{entry.actor_name} ({org})", ""
    return f"{org} user", f"({org} shares activity as organisation only)"


def render(entry, viewer_ctx, *, current_modes: dict | None = None,
           customer_names: dict | None = None) -> RenderedEntry:
    who, note = actor_display(entry, current_modes or {}, customer_names or {})
    own_start = entry.action == "started_clock" and str(entry.actor_id) == str(viewer_ctx.user_id)
    masked = entry.is_incident_detail and not viewer_ctx.is_responder and not own_start
    return RenderedEntry(
        seq=entry.seq, created_at=entry.created_at, who=who, role=ROLE_LABEL.get(entry.actor_role, ""),
        action=entry.action, target=entry.target_label,
        old=MASK if masked and entry.old_value is not None else entry.old_value,
        new=MASK if masked and entry.new_value is not None else entry.new_value,
        reason=MASK if masked and entry.reason else entry.reason,
        masked=masked, note=note,
    )
