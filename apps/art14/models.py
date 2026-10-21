"""Art. 14 events (formerly the pre-built `finding` table; 0 rows, schema change only).

Deadlines are never stored: see apps/art14/deadlines.py (authoritative) and the
Postgres `cra_deadline_check` view (independent check).
"""
from django.db import models
from django.db.models import F, Q

from apps.core.models import TenantScoped

from . import deadlines as engine


class Art14Event(TenantScoped):
    class EventType(models.TextChoices):
        VULNERABILITY = "vulnerability", "Actively exploited vulnerability"
        SEVERE_INCIDENT = "severe_incident", "Severe incident having an impact on the security of the product"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED_REPORTING_COMPLETE = "closed_reporting_complete", "Closed – reporting complete"
        CLOSED_NOT_REPORTABLE = "closed_not_reportable", "Closed – determined not reportable"

    class StartedVia(models.TextChoices):
        LOG_EVENT = "log_event"        # S-8, responder
        START_CLOCK = "start_clock"    # S-8a, any vendor admin

    ref_number = models.PositiveIntegerField()  # E-0001 per vendor tenant
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    awareness_at = models.DateTimeField()
    product = models.ForeignKey("registry.Product", on_delete=models.PROTECT, related_name="+")
    product_version = models.ForeignKey("registry.ProductVersion", on_delete=models.PROTECT, null=True,
                                        blank=True, related_name="+")
    assigned_responder = models.ForeignKey("tenancy.UserAccount", on_delete=models.PROTECT, related_name="+")
    started_by = models.ForeignKey("tenancy.UserAccount", on_delete=models.PROTECT, related_name="+")
    started_via = models.CharField(max_length=16, choices=StartedVia.choices)
    started_at = models.DateTimeField()
    awaiting_responder = models.BooleanField(default=False)
    is_drill = models.BooleanField(default=False)  # immutable after creation (trigger)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.OPEN)
    fix_available_at = models.DateTimeField(null=True, blank=True)
    early_warning_filed_at = models.DateTimeField(null=True, blank=True)
    notification_filed_at = models.DateTimeField(null=True, blank=True)
    final_report_filed_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    close_rationale = models.TextField(blank=True)
    awareness_edit_count = models.PositiveIntegerField(default=0)
    last_recalculated_at = models.DateTimeField(null=True, blank=True)
    row_version = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "art14_event"
        ordering = ["-ref_number"]
        constraints = [
            models.UniqueConstraint(fields=["vendor_tenant", "ref_number"], name="art14_ref_unique"),
            models.CheckConstraint(condition=Q(early_warning_filed_at__isnull=True)
                                   | Q(early_warning_filed_at__gte=F("awareness_at")), name="art14_ew_after_awareness"),
            models.CheckConstraint(condition=Q(notification_filed_at__isnull=True)
                                   | Q(notification_filed_at__gte=F("awareness_at")), name="art14_nt_after_awareness"),
            models.CheckConstraint(condition=Q(final_report_filed_at__isnull=True)
                                   | Q(final_report_filed_at__gte=F("awareness_at")), name="art14_fr_after_awareness"),
            models.CheckConstraint(
                condition=~Q(status="closed_reporting_complete")
                | Q(early_warning_filed_at__isnull=False, notification_filed_at__isnull=False,
                    final_report_filed_at__isnull=False),
                name="art14_complete_needs_filings"),
            models.CheckConstraint(condition=~Q(status="closed_not_reportable") | ~Q(close_rationale=""),
                                   name="art14_not_reportable_needs_rationale"),
            models.CheckConstraint(condition=Q(status="open") | Q(closed_at__isnull=False),
                                   name="art14_closed_has_time"),
        ]

    @property
    def ref(self) -> str:
        return f"E-{self.ref_number:04d}"

    def times(self) -> engine.EventTimes:
        return engine.EventTimes(
            event_type=self.event_type, awareness_at=self.awareness_at,
            fix_available_at=self.fix_available_at, early_warning_filed_at=self.early_warning_filed_at,
            notification_filed_at=self.notification_filed_at, final_report_filed_at=self.final_report_filed_at,
            stopped=self.status == self.Status.CLOSED_NOT_REPORTABLE)


class Art14EventDetail(TenantScoped):
    """Responder-only (RLS requires app.is_responder). Application-level
    encryption of these fields is phase 1b."""

    event = models.OneToOneField(Art14Event, on_delete=models.PROTECT, related_name="detail")
    title = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    affected_component = models.CharField(max_length=300, blank=True)
    vector = models.CharField(max_length=300, blank=True)

    class Meta:
        db_table = "art14_event_detail"


class Art14EventDeployment(TenantScoped):
    """Affected deployments: an incident detail, responder-only."""

    event = models.ForeignKey(Art14Event, on_delete=models.PROTECT, related_name="affected_deployments")
    deployment = models.ForeignKey("registry.Deployment", on_delete=models.PROTECT, related_name="+")

    class Meta:
        db_table = "art14_event_deployment"
        constraints = [models.UniqueConstraint(fields=["event", "deployment"], name="art14_event_dep_unique")]


class Art14UsersInformed(TenantScoped):
    """One row per deployment (design 9.1). Releasing to the customer view (phase 1b)."""

    event = models.ForeignKey(Art14Event, on_delete=models.PROTECT, related_name="users_informed")
    deployment = models.ForeignKey("registry.Deployment", on_delete=models.PROTECT, related_name="+")
    customer_tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.PROTECT, related_name="+")
    informed_at = models.DateTimeField()
    method = models.CharField(max_length=300, blank=True)
    released = models.BooleanField(default=True)
    recorded_by = models.ForeignKey("tenancy.UserAccount", on_delete=models.PROTECT, related_name="+")
    recorded_at = models.DateTimeField()
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    withdrawn_by = models.ForeignKey("tenancy.UserAccount", on_delete=models.PROTECT, null=True, blank=True,
                                     related_name="+")
    withdrawal_reason = models.TextField(blank=True)

    class Meta:
        db_table = "art14_users_informed"
        constraints = [models.UniqueConstraint(fields=["event", "deployment"], name="art14_informed_unique")]


class Art14CustomerReference(TenantScoped):
    """C1: customers get their own reference (INC-1, INC-2...), assigned at release,
    so gaps in vendor references (E-0003 then E-0007) reveal nothing."""

    event = models.ForeignKey(Art14Event, on_delete=models.PROTECT, related_name="+")
    customer_tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.PROTECT, related_name="+")
    number = models.PositiveIntegerField()

    class Meta:
        db_table = "art14_customer_reference"
        constraints = [
            models.UniqueConstraint(fields=["customer_tenant", "number"], name="art14_custref_number"),
            models.UniqueConstraint(fields=["customer_tenant", "event"], name="art14_custref_event"),
        ]


class Art14EventLink(TenantScoped):
    """D7 linked events: table now, screens in phase 1b."""

    from_event = models.ForeignKey(Art14Event, on_delete=models.PROTECT, related_name="+")
    to_event = models.ForeignKey(Art14Event, on_delete=models.PROTECT, related_name="+")
    created_by = models.ForeignKey("tenancy.UserAccount", on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField()

    class Meta:
        db_table = "art14_event_link"
        constraints = [models.CheckConstraint(condition=~Q(from_event=F("to_event")), name="art14_link_not_self")]


class DrillOutcome(TenantScoped):
    """P4 confirmation: would the 24h early warning have been met?"""

    class Answer(models.TextChoices):
        YES = "yes"
        NO = "no"

    event = models.OneToOneField(Art14Event, on_delete=models.PROTECT, related_name="drill_outcome")
    early_warning_would_be_met = models.CharField(max_length=3, choices=Answer.choices)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey("tenancy.UserAccount", on_delete=models.PROTECT, related_name="+")
    recorded_at = models.DateTimeField()

    class Meta:
        db_table = "drill_outcome"
