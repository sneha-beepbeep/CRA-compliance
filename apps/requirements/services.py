"""Requirement status changes (R-1). Statuses describe records; they never judge."""
from __future__ import annotations

from collections import Counter

from django.db import transaction

from apps.audit.log import record
from apps.core import clock

from .models import RATIONALE_MIN, EvidenceItem, RequirementStatus

ORDER = ["evidence_attached", "evidence_stale", "not_applicable", "in_progress", "not_started"]
LABEL = {"not_started": "not started", "in_progress": "in progress", "evidence_attached": "evidence attached",
         "evidence_stale": "evidence stale", "not_applicable": "not applicable"}


class StatusError(ValueError):
    def __init__(self, message, field=None):
        super().__init__(message)
        self.message, self.field = message, field


def summary(statuses) -> dict:
    counts = Counter(s.display_status for s in statuses)
    total = sum(counts.values())
    return {"total": total, "attached": counts["evidence_attached"],
            "breakdown": [(LABEL[k], counts[k]) for k in ORDER]}


@transaction.atomic
def change_status(request, status_id, *, status: str, review_by=None, rationale: str = "", note: str = "",
                  row_version: int) -> RequirementStatus:
    s = RequirementStatus.objects.select_for_update(of=("self",)).select_related("requirement", "updated_by").get(pk=status_id)
    if s.row_version != row_version:
        who = s.updated_by.display_name if s.updated_by else "someone"
        when = s.updated_at.strftime("%H:%M UTC") if s.updated_at else ""
        raise StatusError(f"{who} changed this at {when}. Review their change before saving yours.")
    if status not in RequirementStatus.Status.values:
        raise StatusError("Choose a status.", "status")
    if status == "evidence_attached":
        if not s.evidence.exists():
            raise StatusError("Add at least one evidence item first.", "status")
        if review_by is None:
            raise StatusError("A review-by date is required.", "review_by")
    if status == "not_applicable" and len(rationale.strip()) < RATIONALE_MIN:
        raise StatusError(f"A rationale of at least {RATIONALE_MIN} characters is required. It is visible to "
                          "your customers.", "rationale")
    old = {"status": s.display_status, "review_by": s.review_by, "rationale": s.rationale}
    s.status = status
    s.review_by = review_by if status == "evidence_attached" else (review_by or s.review_by)
    # QA-12: the customer-visible rationale only exists while the status is N/A (history stays in the audit).
    s.rationale = rationale.strip() if status == "not_applicable" else ""
    s.updated_by, s.updated_at = request.user, clock.now()
    s.row_version += 1
    s.carried_forward_from = None
    s.save()
    record(request, area="requirements", action="status_change", target=s, target_label=s.requirement.citation,
           old=old, new={"status": s.display_status, "review_by": s.review_by, "rationale": s.rationale},
           reason=note)
    return s


@transaction.atomic
def add_evidence(request, *, title, type, evidence_date, url="", requirement_status=None, ai_risk=None):
    parent = requirement_status or ai_risk
    item = EvidenceItem.objects.create(
        vendor_tenant_id=parent.vendor_tenant_id, requirement_status=requirement_status, ai_risk=ai_risk,
        title=title.strip(), type=type, evidence_date=evidence_date, url=url.strip(), added_by=request.user,
        added_at=clock.now())
    label = requirement_status.requirement.citation if requirement_status else ai_risk.name
    record(request, area="requirements" if requirement_status else "airisks", action="added_evidence",
           target=item, target_label=label, new={"title": item.title, "type": type, "date": evidence_date})
    return item
