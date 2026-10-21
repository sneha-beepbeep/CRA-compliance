"""Shared model bases. Not an installed app; imported by the domain apps."""
import uuid

from django.db import models


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TenantScoped(UUIDModel):
    """Every tenant table carries vendor_tenant_id; RLS policies key on it."""

    vendor_tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.PROTECT, related_name="+",
                                      db_column="vendor_tenant_id")

    class Meta:
        abstract = True
