"""Requirement status per product version (R-1, D3) and evidence items (links only, C5)."""
from datetime import date, datetime, timezone

from django.db import models
from django.db.models import Q

from apps.core.models import TenantScoped

RATIONALE_MIN = 20


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def is_stale(review_by: date | None, today: date | None = None) -> bool:
    """'Evidence stale' is computed when read: set at 00:00 UTC on the day after review-by."""
    return review_by is not None and (today or utc_today()) > review_by


class RequirementStatus(TenantScoped):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "not started"
        IN_PROGRESS = "in_progress", "in progress"
        EVIDENCE_ATTACHED = "evidence_attached", "evidence attached"
        NOT_APPLICABLE = "not_applicable", "not applicable (with rationale)"
        # "evidence stale" is deliberately not a stored choice: it is system-only
        # and computed from review_by (design 6.1, deviation 5).

    version = models.ForeignKey("registry.ProductVersion", on_delete=models.PROTECT, related_name="requirement_statuses")
    requirement = models.ForeignKey("catalog.Requirement", on_delete=models.PROTECT, related_name="+")
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.NOT_STARTED)
    review_by = models.DateField(null=True, blank=True)
    rationale = models.TextField(blank=True)  # customer-visible (D2)
    updated_by = models.ForeignKey("tenancy.UserAccount", on_delete=models.PROTECT, null=True, related_name="+")
    updated_at = models.DateTimeField(null=True, blank=True)
    row_version = models.PositiveIntegerField(default=0)  # optimistic locking
    carried_forward_from = models.ForeignKey("registry.ProductVersion", on_delete=models.PROTECT, null=True,
                                             blank=True, related_name="+")
    carried_forward_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "requirement_status"
        constraints = [
            models.UniqueConstraint(fields=["version", "requirement"], name="req_status_unique"),
            models.CheckConstraint(condition=~Q(status="evidence_attached") | Q(review_by__isnull=False),
                                   name="req_evidence_needs_review_by"),
            models.CheckConstraint(condition=~Q(status="not_applicable")
                                   | Q(rationale__regex=r"^[\s\S]{%d,}$" % RATIONALE_MIN),
                                   name="req_na_needs_rationale"),
        ]

    @property
    def display_status(self) -> str:
        if self.status == self.Status.EVIDENCE_ATTACHED and is_stale(self.review_by):
            return "evidence_stale"
        return self.status



class EvidenceItem(TenantScoped):
    class Type(models.TextChoices):
        DOCUMENT = "document"
        LINK = "link"
        TEST_REPORT = "test_report", "test report"
        POLICY = "policy"
        OTHER = "other"

    requirement_status = models.ForeignKey(RequirementStatus, on_delete=models.PROTECT, null=True, blank=True,
                                           related_name="evidence")
    ai_risk = models.ForeignKey("airisks.AIRisk", on_delete=models.PROTECT, null=True, blank=True,
                                related_name="evidence")
    title = models.CharField(max_length=300)
    type = models.CharField(max_length=16, choices=Type.choices)
    evidence_date = models.DateField()
    url = models.URLField(max_length=1000, blank=True)  # never shown to customers (D2)
    added_by = models.ForeignKey("tenancy.UserAccount", on_delete=models.PROTECT, related_name="+")
    added_at = models.DateTimeField()

    class Meta:
        db_table = "evidence_item"
        ordering = ["-evidence_date", "title"]
        constraints = [
            models.CheckConstraint(
                condition=(Q(requirement_status__isnull=False, ai_risk__isnull=True)
                           | Q(requirement_status__isnull=True, ai_risk__isnull=False)),
                name="evidence_one_target"),
        ]
