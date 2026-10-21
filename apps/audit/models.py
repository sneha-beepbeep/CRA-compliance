"""Append-only audit trail (NFR-3).

Enforced three ways (db/sql/audit_append_only.sql): application roles have no
UPDATE/DELETE/TRUNCATE rights; a trigger rejects UPDATE and DELETE for every
role; and each row carries a per-vendor SHA-256 hash chain set by a trigger.
The real actor is always stored (D9); masking and anonymisation are applied
when rendering (apps/audit/render.py), never by deleting data.
"""
from django.db import models

from apps.core.models import TenantScoped


class AuditEvent(TenantScoped):
    seq = models.BigIntegerField(null=True, editable=False)  # set by trigger
    created_at = models.DateTimeField(null=True, editable=False)  # set by trigger (server clock)
    actor = models.ForeignKey("tenancy.UserAccount", on_delete=models.PROTECT, null=True, related_name="+")
    actor_tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.PROTECT, null=True, related_name="+")
    actor_name = models.CharField(max_length=200)
    actor_role = models.CharField(max_length=32)  # vendor_admin / responder / customer_admin / system
    # D9: the customer's activity-sharing mode at the time of the action.
    shared_as = models.CharField(max_length=16, blank=True)
    area = models.CharField(max_length=32)
    action = models.CharField(max_length=64)
    target_type = models.CharField(max_length=64, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    target_label = models.CharField(max_length=300, blank=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    reason = models.TextField(blank=True)
    # True when old/new values are incident details: masked for non-responders.
    is_incident_detail = models.BooleanField(default=False)
    is_drill = models.BooleanField(default=False)
    import_id = models.UUIDField(null=True, blank=True)
    export_id = models.UUIDField(null=True, blank=True)
    prev_hash = models.CharField(max_length=64, blank=True, editable=False)
    hash = models.CharField(max_length=64, blank=True, editable=False)

    class Meta:
        db_table = "audit_event"
        ordering = ["-seq"]
