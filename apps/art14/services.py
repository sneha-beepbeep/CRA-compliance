"""Art. 14 event operations. All writes are audited; views stay thin."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import IntegrityError, transaction
from django.db.models import Max

from apps.audit.log import record
from apps.core import clock
from apps.tenancy.models import RoleGrant, SystemSetting, UserAccount

from . import deadlines as engine
from .models import (Art14Event, Art14EventDeployment, Art14EventDetail, DrillOutcome)

REASON_MIN = 20


class EventError(ValueError):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field


class ConflictError(EventError):
    pass


def month_rule() -> str:
    return SystemSetting.get("month_rule")


def real_events_enabled() -> bool:
    """C6: drills only until the pentest passes. Operators flip this setting."""
    return bool(SystemSetting.get("real_events_enabled") or False)


def responders(vendor_tenant_id) -> list[UserAccount]:
    ids = RoleGrant.objects.filter(vendor_tenant_id=vendor_tenant_id, role=RoleGrant.Role.INCIDENT_RESPONDER,
                                   revoked_at__isnull=True).values_list("user_id", flat=True)
    return list(UserAccount.objects.filter(id__in=list(ids), is_active=True).order_by("display_name"))


def is_responder(user_id) -> bool:
    return RoleGrant.objects.filter(user_id=user_id, role=RoleGrant.Role.INCIDENT_RESPONDER,
                                    revoked_at__isnull=True).exists()


def _minute(dt: datetime | None) -> datetime | None:
    return dt.replace(second=0, microsecond=0) if dt else None


def _event_label(e: Art14Event) -> str:
    return f"{'DRILL ' if e.is_drill else ''}{e.ref} · {e.get_event_type_display().lower()}"


@transaction.atomic
def create_event(request, *, event_type: str, awareness_at: datetime, product, assignee: UserAccount,
                 is_drill: bool, via: str, version=None, deployments=(), title: str = "",
                 description: str = "", component: str = "", vector: str = "") -> Art14Event:
    ctx = request.tenant_ctx
    if not is_drill and not real_events_enabled():
        raise EventError("Only drills can be logged until real incident data is enabled for this workspace "
                         "(pilot agreement).")
    if not is_responder(assignee.pk) or str(assignee.vendor_tenant_id) != ctx.vendor_tenant_id:
        raise EventError("Choose an incident responder.", "assignee")
    if via == Art14Event.StartedVia.START_CLOCK and any([title, description, component, vector, deployments]):
        raise EventError("Starting a clock takes no incident details.")  # S-8a has no free text
    awareness_at = _minute(awareness_at)
    now = clock.now()
    if awareness_at > now.replace(second=0, microsecond=0) + timedelta(minutes=1):
        raise EventError("Awareness time can't be in the future.", "awareness")
    for _ in range(3):
        nxt = (Art14Event.objects.aggregate(m=Max("ref_number"))["m"] or 0) + 1
        try:
            with transaction.atomic():
                ev = Art14Event.objects.create(
                    vendor_tenant_id=ctx.vendor_tenant_id, ref_number=nxt, event_type=event_type,
                    awareness_at=awareness_at, product=product, product_version=version,
                    assigned_responder=assignee, started_by=request.user, started_via=via, started_at=now,
                    awaiting_responder=(via == Art14Event.StartedVia.START_CLOCK
                                        and str(assignee.pk) != str(request.user.pk)),
                    is_drill=is_drill)
            break
        except IntegrityError:
            continue
    else:  # pragma: no cover
        raise EventError("Event not logged. Clocks have not started. Try again.")
    if via == Art14Event.StartedVia.LOG_EVENT:
        Art14EventDetail.objects.create(vendor_tenant_id=ctx.vendor_tenant_id, event=ev, title=title,
                                        description=description, affected_component=component, vector=vector)
        for d in deployments:
            Art14EventDeployment.objects.create(vendor_tenant_id=ctx.vendor_tenant_id, event=ev, deployment=d)
    started = {"type": event_type, "product": product.name, "awareness_at": awareness_at,
               "assigned": assignee.display_name, "drill": is_drill}
    record(request, area="art14", action="started_clock" if via == "start_clock" else "logged_event",
           target=ev, target_label=_event_label(ev), new=started, incident_detail=True, drill=is_drill)
    return ev


def _locked(event_id, row_version: int | None) -> Art14Event:
    ev = Art14Event.objects.select_for_update().get(pk=event_id)
    if row_version is not None and ev.row_version != row_version:
        raise ConflictError("This event was changed by someone else since you opened it. Review the change "
                            "before saving yours.")
    return ev


def _save(ev: Art14Event, fields: list[str]):
    ev.row_version += 1
    ev.save(update_fields=fields + ["row_version"])


@transaction.atomic
def record_time(request, event_id, *, which: str, when: datetime, reason: str = "",
                row_version: int | None = None) -> Art14Event:
    """Record a filing time (early warning, notification, final report) or the fix time."""
    field = {"early_warning": "early_warning_filed_at", "notification": "notification_filed_at",
             "final_report": "final_report_filed_at", "fix": "fix_available_at"}[which]
    ev = _locked(event_id, row_version)
    when = _minute(when)
    if when > clock.now() + timedelta(seconds=60):
        raise EventError("This time can't be in the future.", "when")
    if field != "fix_available_at" and when < ev.awareness_at:
        raise EventError("A filing time can't be earlier than the awareness time.", "when")
    old = getattr(ev, field)
    if old is not None and len(reason.strip()) < REASON_MIN:
        raise EventError(f"Correcting a recorded time needs a reason (at least {REASON_MIN} characters).",
                         "reason")
    setattr(ev, field, when)
    _save(ev, [field])
    record(request, area="art14", action=f"recorded_{which}" if old is None else f"corrected_{which}",
           target=ev, target_label=_event_label(ev), old={field: old}, new={field: when}, reason=reason,
           incident_detail=True, drill=ev.is_drill)
    return ev


def preview_awareness(ev: Art14Event, new_awareness: datetime, now: datetime | None = None):
    after = engine.EventTimes(**{**ev.times().__dict__, "awareness_at": _minute(new_awareness)})
    return engine.preview_change(ev.times(), after, now or clock.now(), month_rule())


@transaction.atomic
def edit_awareness(request, event_id, *, new_awareness: datetime, reason: str, row_version: int) -> Art14Event:
    if len(reason.strip()) < REASON_MIN:
        raise EventError(f"Give a reason (at least {REASON_MIN} characters).", "reason")
    ev = _locked(event_id, row_version)
    new_awareness = _minute(new_awareness)
    if new_awareness > clock.now() + timedelta(seconds=60):
        raise EventError("Awareness time can't be in the future.", "awareness")
    filings = [t for t in (ev.early_warning_filed_at, ev.notification_filed_at, ev.final_report_filed_at) if t]
    if any(t < new_awareness for t in filings):
        raise EventError("Awareness time can't be later than a recorded filing time.", "awareness")
    old = ev.awareness_at
    ev.awareness_at = new_awareness
    ev.awareness_edit_count += 1
    ev.last_recalculated_at = clock.now()
    _save(ev, ["awareness_at", "awareness_edit_count", "last_recalculated_at"])
    record(request, area="art14", action="edited_awareness_time", target=ev, target_label=_event_label(ev),
           old={"awareness_at": old}, new={"awareness_at": new_awareness}, reason=reason,
           incident_detail=True, drill=ev.is_drill)
    return ev


@transaction.atomic
def close_event(request, event_id, *, outcome: str, rationale: str = "", row_version: int) -> Art14Event:
    ev = _locked(event_id, row_version)
    if ev.status != Art14Event.Status.OPEN:
        raise EventError("This event is already closed.")
    if outcome == Art14Event.Status.CLOSED_REPORTING_COMPLETE:
        if not (ev.early_warning_filed_at and ev.notification_filed_at and ev.final_report_filed_at):
            raise EventError("Record all three filing times before closing as reporting complete.")
    elif outcome == Art14Event.Status.CLOSED_NOT_REPORTABLE:
        if len(rationale.strip()) < REASON_MIN:
            raise EventError(f"Give a rationale (at least {REASON_MIN} characters).", "rationale")
    else:
        raise EventError("Choose how to close the event.", "outcome")
    ev.status, ev.closed_at, ev.close_rationale = outcome, clock.now(), rationale.strip()
    _save(ev, ["status", "closed_at", "close_rationale"])
    record(request, area="art14", action="closed_event", target=ev, target_label=_event_label(ev),
           new={"status": outcome}, reason=rationale, incident_detail=True, drill=ev.is_drill)
    return ev


@transaction.atomic
def reopen_event(request, event_id, *, reason: str, row_version: int) -> Art14Event:
    if len(reason.strip()) < REASON_MIN:
        raise EventError(f"Give a reason (at least {REASON_MIN} characters).", "reason")
    ev = _locked(event_id, row_version)
    if ev.status == Art14Event.Status.OPEN:
        raise EventError("This event is already open.")
    old = ev.status
    ev.status, ev.closed_at, ev.close_rationale = Art14Event.Status.OPEN, None, ""
    _save(ev, ["status", "closed_at", "close_rationale"])
    record(request, area="art14", action="reopened_event", target=ev, target_label=_event_label(ev),
           old={"status": old}, new={"status": "open"}, reason=reason, incident_detail=True, drill=ev.is_drill)
    return ev


@transaction.atomic
def reassign(request, event_id, *, assignee: UserAccount, take_over: bool = False) -> Art14Event:
    ev = _locked(event_id, None)
    if not is_responder(assignee.pk):
        raise EventError("Choose an incident responder.", "assignee")
    old = ev.assigned_responder.display_name
    ev.assigned_responder = assignee
    ev.awaiting_responder = not take_over and str(assignee.pk) != str(request.user.pk)
    _save(ev, ["assigned_responder", "awaiting_responder"])
    record(request, area="art14", action="took_over" if take_over else "reassigned_responder", target=ev,
           target_label=_event_label(ev), old={"assigned": old}, new={"assigned": assignee.display_name},
           drill=ev.is_drill)
    return ev


def record_detail_view(request, ev: Art14Event) -> None:
    """Every view of incident details is audited (NFR-3); the assigned responder's
    first view clears the awaiting-responder flag (8.3a)."""
    if ev.awaiting_responder and str(ev.assigned_responder_id) == str(request.user.pk):
        Art14Event.objects.filter(pk=ev.pk).update(awaiting_responder=False)
        ev.awaiting_responder = False
    record(request, area="art14", action="viewed_details", target=ev, target_label=_event_label(ev),
           drill=ev.is_drill)


@transaction.atomic
def update_details(request, ev: Art14Event, *, title: str, description: str, component: str, vector: str,
                   version=None, deployments=()):
    detail, _ = Art14EventDetail.objects.get_or_create(event=ev, defaults={"vendor_tenant_id": ev.vendor_tenant_id})
    old = {"title": detail.title, "description": detail.description, "component": detail.affected_component,
           "vector": detail.vector, "version": ev.product_version.label if ev.product_version else None,
           "deployments": sorted(d.deployment.label for d in ev.affected_deployments.select_related("deployment"))}
    detail.title, detail.description, detail.affected_component, detail.vector = title, description, component, vector
    detail.save()
    if version is not None or ev.product_version_id:
        ev.product_version = version
        _save(ev, ["product_version"])
    Art14EventDeployment.objects.filter(event=ev).delete()
    for d in deployments:
        Art14EventDeployment.objects.create(vendor_tenant_id=ev.vendor_tenant_id, event=ev, deployment=d)
    new = {"title": title, "description": description, "component": component, "vector": vector,
           "version": version.label if version else None, "deployments": sorted(d.label for d in deployments)}
    record(request, area="art14", action="edited_details", target=ev, target_label=_event_label(ev),
           old=old, new=new, incident_detail=True, drill=ev.is_drill)


@transaction.atomic
def record_drill_outcome(request, ev: Art14Event, *, answer: str, notes: str) -> DrillOutcome:
    if not ev.is_drill:
        raise EventError("Only drills have a drill outcome.")
    if hasattr(ev, "drill_outcome"):
        raise EventError("The drill outcome is already recorded.")
    out = DrillOutcome.objects.create(vendor_tenant_id=ev.vendor_tenant_id, event=ev,
                                      early_warning_would_be_met=answer, notes=notes,
                                      recorded_by=request.user, recorded_at=clock.now())
    record(request, area="art14", action="recorded_drill_outcome", target=ev, target_label=_event_label(ev),
           new={"early_warning_would_be_met": answer, "notes": notes}, drill=True)
    return out


# ---------------------------------------------------------------------------
# Clock strip (S-1) and event list rows (S-7)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ClockRow:
    event: Art14Event | None
    deadlines: engine.Deadlines | None
    next_clock: engine.Clock | None
    tier: engine.Tier
    message: str = ""  # for the special "no responder" rows

    @property
    def sort_key(self):
        due = self.next_clock.due_at if self.next_clock else datetime.min.replace(tzinfo=engine.UTC)
        ev = self.event
        return (engine.TIER_ORDER[self.tier], bool(ev and ev.is_drill), not bool(ev and ev.awaiting_responder), due)


def event_rows(events, now: datetime | None = None) -> list[ClockRow]:
    now = now or clock.now()
    rule = month_rule()
    rows = []
    for ev in events:
        d = engine.compute(ev.times(), now, rule)
        rows.append(ClockRow(ev, d, d.next_running(), engine.tier(d)))
    return rows


def strip_rows(vendor_tenant_id, now: datetime | None = None) -> list[ClockRow]:
    events = (Art14Event.objects.filter(status=Art14Event.Status.OPEN)
              .select_related("assigned_responder", "started_by", "product"))
    rows = [r for r in event_rows(events, now) if r.next_clock is not None]
    resp_ids = {str(u.pk) for u in responders(vendor_tenant_id)}
    special = []
    if not resp_ids:
        special.append(ClockRow(None, None, None, engine.Tier.OVERDUE,
                                "No incident responder assigned. Clocks can't be routed."))
    out = []
    for r in rows:
        if str(r.event.assigned_responder_id) not in resp_ids and resp_ids:
            out.append(ClockRow(r.event, r.deadlines, r.next_clock, engine.Tier.OVERDUE,
                                "Assigned responder no longer has the role"))
        else:
            out.append(r)
    return special + sorted(out, key=lambda r: r.sort_key)
