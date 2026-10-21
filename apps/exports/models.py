"""Export records: ID plus SHA-256 of the file as generated. Files are not stored."""
from django.db import models

from apps.core.models import TenantScoped


class ExportRecord(TenantScoped):
    class Kind(models.TextChoices):
        CUSTOMER_PDF = "customer_pdf"
        CUSTOMER_CSV = "customer_csv"
        VENDOR_STATUS = "vendor_status"
        AUDIT_CSV = "audit_csv"
        AUDIT_JSON = "audit_json"

    kind = models.CharField(max_length=16, choices=Kind.choices)
    deployment = models.ForeignKey("registry.Deployment", on_delete=models.PROTECT, null=True, blank=True,
                                   related_name="+")
    sha256 = models.CharField(max_length=64)
    generated_by = models.ForeignKey("tenancy.UserAccount", on_delete=models.PROTECT, related_name="+")
    generated_by_tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.PROTECT, related_name="+")
    generated_at = models.DateTimeField()

    class Meta:
        db_table = "export_record"
