"""CSV import batches: preview, then all-or-nothing (screens slip to pilot week 1)."""
from django.db import models

from apps.core.models import TenantScoped


class ImportBatch(TenantScoped):
    class Target(models.TextChoices):
        REQUIREMENTS = "requirements"
        AI_RISKS = "ai_risks"

    class State(models.TextChoices):
        PREVIEWED = "previewed"
        APPLIED = "applied"
        ABANDONED = "abandoned"

    version = models.ForeignKey("registry.ProductVersion", on_delete=models.PROTECT, related_name="+")
    target = models.CharField(max_length=16, choices=Target.choices)
    filename = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64)
    state = models.CharField(max_length=16, choices=State.choices, default=State.PREVIEWED)
    rows_read = models.PositiveIntegerField(default=0)
    changes = models.PositiveIntegerField(default=0)
    errors = models.JSONField(default=list)
    created_by = models.ForeignKey("tenancy.UserAccount", on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField()
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "import_batch"
