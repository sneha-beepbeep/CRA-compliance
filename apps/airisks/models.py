"""AI-specific risk register (R-2, OQ3): handling stages, never scores."""
from django.db import models
from django.db.models import Q

from apps.core.models import TenantScoped
from apps.requirements.models import is_stale


class AIRisk(TenantScoped):
    class Stage(models.TextChoices):
        NOT_ASSESSED = "not_assessed", "not assessed"
        ASSESSED_PLANNED = "assessed_planned", "assessed – treatment planned"
        TREATMENT_IN_PLACE = "treatment_in_place", "treatment in place – evidence attached"
        ACCEPTED = "accepted", "accepted with rationale"
        NOT_APPLICABLE = "not_applicable", "not applicable with rationale"
        # "evidence stale" is computed from review_by, never stored.

    version = models.ForeignKey("registry.ProductVersion", on_delete=models.PROTECT, related_name="ai_risks")
    taxonomy_item = models.ForeignKey("catalog.TaxonomyItem", on_delete=models.PROTECT, null=True, blank=True)
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    attack_class = models.CharField(max_length=64, blank=True)
    stage = models.CharField(max_length=32, choices=Stage.choices, default=Stage.NOT_ASSESSED)
    planned_treatment = models.TextField(blank=True)
    rationale = models.TextField(blank=True)  # customer-visible (D2)
    review_by = models.DateField(null=True, blank=True)
    owner = models.ForeignKey("tenancy.UserAccount", on_delete=models.PROTECT, null=True, blank=True,
                              related_name="+")
    last_reviewed_on = models.DateField(null=True, blank=True)
    updated_by = models.ForeignKey("tenancy.UserAccount", on_delete=models.PROTECT, null=True, related_name="+")
    updated_at = models.DateTimeField(null=True, blank=True)
    row_version = models.PositiveIntegerField(default=0)
    carried_forward_from = models.ForeignKey("registry.ProductVersion", on_delete=models.PROTECT, null=True,
                                             blank=True, related_name="+")

    class Meta:
        db_table = "ai_risk"
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(condition=~Q(stage="assessed_planned") | ~Q(planned_treatment=""),
                                   name="airisk_planned_needs_treatment"),
            models.CheckConstraint(condition=~Q(stage="treatment_in_place") | Q(review_by__isnull=False),
                                   name="airisk_in_place_needs_review_by"),
            models.CheckConstraint(condition=~Q(stage__in=["accepted", "not_applicable"]) | ~Q(rationale=""),
                                   name="airisk_rationale_required"),
        ]

    @property
    def display_stage(self) -> str:
        if self.stage == self.Stage.TREATMENT_IN_PLACE and is_stale(self.review_by):
            return "evidence_stale"
        return self.stage

    @property
    def last_tested(self):
        """Date of the most recent evidence of type 'test report' (design 7.1)."""
        item = self.evidence.filter(type="test_report").order_by("-evidence_date").first()
        return item.evidence_date if item else None


class AIRiskRequirementLink(TenantScoped):
    """Informational only: never changes either side's status (design 6.2)."""

    ai_risk = models.ForeignKey(AIRisk, on_delete=models.CASCADE, related_name="requirement_links")
    requirement = models.ForeignKey("catalog.Requirement", on_delete=models.PROTECT, related_name="+")

    class Meta:
        db_table = "ai_risk_requirement_link"
        constraints = [models.UniqueConstraint(fields=["ai_risk", "requirement"], name="airisk_req_link_unique")]
