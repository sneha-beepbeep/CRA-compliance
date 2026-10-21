"""CRA Art. 14 deadline engine (authoritative).

Pure Python, no Django or database imports, so it can be unit-, property- and
golden-tested in isolation. Deadlines are computed when read and never stored.

Rules (design spec 8.1, technical plan "Deadline engine"):

* early warning   = awareness + 24 elapsed hours        (both event types)
* notification    = awareness + 72 elapsed hours        (both event types)
* final report    = fix or mitigation available + 14 days (actively exploited vulnerability)
                  = notification filing + 1 month       (severe incident)

"1 month" follows the configured month rule:

* ``calendar_clamp_utc`` (default, D10, pending legal confirmation D-4): same
  calendar day next month in UTC, clamped to the last day of that month, at the
  same UTC time of day.
* ``days_30``: 30 x 24 elapsed hours.

States: ``not started``, ``open``, ``met``, ``late``, ``overdue``, ``stopped``.

* A filing time recorded at or before the due time is ``met``; after it, ``late``.
* With no filing: ``overdue`` once ``now`` is strictly after the due time,
  otherwise ``open``. At exactly the due minute the deadline is still ``open``.
* ``not started``: the clock's start time is not recorded.
* ``stopped``: the event was closed as not reportable and this clock had no
  filing. Clocks with a recorded filing keep ``met``/``late`` (a recorded fact).

All times are timezone-aware and handled in UTC at minute resolution (NFR-4).
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum

UTC = timezone.utc

EARLY_WARNING_HOURS = 24
NOTIFICATION_HOURS = 72
VULN_FINAL_REPORT_DAYS = 14
DAYS_30 = 30


class EventType(StrEnum):
    VULNERABILITY = "vulnerability"  # actively exploited vulnerability, CRA Art. 14(1)
    SEVERE_INCIDENT = "severe_incident"  # CRA Art. 14(3)


class MonthRule(StrEnum):
    CALENDAR_CLAMP_UTC = "calendar_clamp_utc"
    DAYS_30 = "days_30"


DEFAULT_MONTH_RULE = MonthRule.CALENDAR_CLAMP_UTC


class ClockKind(StrEnum):
    EARLY_WARNING = "early_warning"
    NOTIFICATION = "notification"
    FINAL_REPORT = "final_report"


class State(StrEnum):
    NOT_STARTED = "not started"
    OPEN = "open"
    MET = "met"
    LATE = "late"
    OVERDUE = "overdue"
    STOPPED = "stopped"


class Warning_(StrEnum):
    # C7: a fix recorded before awareness is allowed, computed as specified,
    # shown with a warning and referred to legal.
    FIX_BEFORE_AWARENESS = "fix_before_awareness"


class DeadlineInputError(ValueError):
    """Raised for inputs the engine refuses to compute with."""


def _utc_minute(value: datetime | None, name: str) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise DeadlineInputError(f"{name} must be timezone-aware")
    return value.astimezone(UTC).replace(second=0, microsecond=0)


def add_one_month(start: datetime, rule: MonthRule | str = DEFAULT_MONTH_RULE) -> datetime:
    """Add one month to ``start`` (aware) under ``rule``. Result is in UTC."""
    rule = MonthRule(rule)
    start = _utc_minute(start, "start")
    if rule is MonthRule.DAYS_30:
        return start + timedelta(days=DAYS_30)
    year, month = (start.year + 1, 1) if start.month == 12 else (start.year, start.month + 1)
    last_day = calendar.monthrange(year, month)[1]
    return start.replace(year=year, month=month, day=min(start.day, last_day))


@dataclass(frozen=True)
class EventTimes:
    """Everything the engine needs about one event. All datetimes aware."""

    event_type: EventType | str
    awareness_at: datetime
    fix_available_at: datetime | None = None
    early_warning_filed_at: datetime | None = None
    notification_filed_at: datetime | None = None
    final_report_filed_at: datetime | None = None
    stopped: bool = False  # closed as "determined not reportable"

    def normalised(self) -> "EventTimes":
        if self.awareness_at is None:
            raise DeadlineInputError("awareness_at is required")
        return EventTimes(
            event_type=EventType(self.event_type),
            awareness_at=_utc_minute(self.awareness_at, "awareness_at"),
            fix_available_at=_utc_minute(self.fix_available_at, "fix_available_at"),
            early_warning_filed_at=_utc_minute(self.early_warning_filed_at, "early_warning_filed_at"),
            notification_filed_at=_utc_minute(self.notification_filed_at, "notification_filed_at"),
            final_report_filed_at=_utc_minute(self.final_report_filed_at, "final_report_filed_at"),
            stopped=bool(self.stopped),
        )


@dataclass(frozen=True)
class Clock:
    kind: ClockKind
    start_at: datetime | None
    due_at: datetime | None
    filed_at: datetime | None
    state: State

    @property
    def is_running(self) -> bool:
        return self.state in (State.OPEN, State.OVERDUE)


@dataclass(frozen=True)
class Deadlines:
    early_warning: Clock
    notification: Clock
    final_report: Clock
    warnings: tuple[Warning_, ...] = field(default_factory=tuple)

    @property
    def clocks(self) -> tuple[Clock, Clock, Clock]:
        return (self.early_warning, self.notification, self.final_report)

    def next_running(self) -> Clock | None:
        """The next unfiled deadline (open or overdue), soonest due first."""
        running = [c for c in self.clocks if c.is_running]
        return min(running, key=lambda c: c.due_at) if running else None


def _state(start: datetime | None, due: datetime | None, filed: datetime | None,
           now: datetime, stopped: bool) -> State:
    if filed is not None and due is not None:
        return State.MET if filed <= due else State.LATE
    if stopped:
        return State.STOPPED
    if start is None or due is None:
        return State.NOT_STARTED
    return State.OVERDUE if now > due else State.OPEN


def final_report_start(times: EventTimes) -> datetime | None:
    t = times.normalised()
    if t.event_type is EventType.VULNERABILITY:
        return t.fix_available_at
    return t.notification_filed_at


def compute(times: EventTimes, now: datetime,
            month_rule: MonthRule | str = DEFAULT_MONTH_RULE) -> Deadlines:
    """Compute all three Art. 14 clocks for one event at server time ``now``."""
    t = times.normalised()
    now = _utc_minute(now, "now")

    ew_due = t.awareness_at + timedelta(hours=EARLY_WARNING_HOURS)
    nt_due = t.awareness_at + timedelta(hours=NOTIFICATION_HOURS)

    if t.event_type is EventType.VULNERABILITY:
        fr_start = t.fix_available_at
        fr_due = fr_start + timedelta(days=VULN_FINAL_REPORT_DAYS) if fr_start else None
    else:
        fr_start = t.notification_filed_at
        fr_due = add_one_month(fr_start, month_rule) if fr_start else None

    warnings: list[Warning_] = []
    if (t.event_type is EventType.VULNERABILITY and t.fix_available_at is not None
            and t.fix_available_at < t.awareness_at):
        warnings.append(Warning_.FIX_BEFORE_AWARENESS)

    return Deadlines(
        early_warning=Clock(ClockKind.EARLY_WARNING, t.awareness_at, ew_due, t.early_warning_filed_at,
                            _state(t.awareness_at, ew_due, t.early_warning_filed_at, now, t.stopped)),
        notification=Clock(ClockKind.NOTIFICATION, t.awareness_at, nt_due, t.notification_filed_at,
                           _state(t.awareness_at, nt_due, t.notification_filed_at, now, t.stopped)),
        final_report=Clock(ClockKind.FINAL_REPORT, fr_start, fr_due, t.final_report_filed_at,
                           _state(fr_start, fr_due, t.final_report_filed_at, now, t.stopped)),
        warnings=tuple(warnings),
    )


# ---------------------------------------------------------------------------
# Before/after previews (S-11 awareness edit, S-12 reclassify)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ClockChange:
    kind: ClockKind
    before: Clock
    after: Clock

    @property
    def due_changed(self) -> bool:
        return self.before.due_at != self.after.due_at

    @property
    def state_changed(self) -> bool:
        return self.before.state != self.after.state


def preview_change(before: EventTimes, after: EventTimes, now: datetime,
                   month_rule: MonthRule | str = DEFAULT_MONTH_RULE) -> tuple[ClockChange, ...]:
    b = compute(before, now, month_rule)
    a = compute(after, now, month_rule)
    return tuple(ClockChange(cb.kind, cb, ca) for cb, ca in zip(b.clocks, a.clocks))


# ---------------------------------------------------------------------------
# Presentation helpers that are pure functions of the computed clocks
# ---------------------------------------------------------------------------

class Tier(StrEnum):
    """Clock-strip emphasis tiers (design 10.3), most urgent first."""

    OVERDUE = "overdue"
    EARLY_WARNING_OPEN = "early_warning_open"
    NOTIFICATION_OPEN = "notification_open"
    FINAL_REPORT_OPEN = "final_report_open"
    NONE = "none"


TIER_ORDER = {t: i for i, t in enumerate(Tier)}


def tier(deadlines: Deadlines) -> Tier:
    running = [c for c in deadlines.clocks if c.is_running]
    if any(c.state is State.OVERDUE for c in running):
        return Tier.OVERDUE
    kinds = {c.kind for c in running}
    if ClockKind.EARLY_WARNING in kinds:
        return Tier.EARLY_WARNING_OPEN
    if ClockKind.NOTIFICATION in kinds:
        return Tier.NOTIFICATION_OPEN
    if ClockKind.FINAL_REPORT in kinds:
        return Tier.FINAL_REPORT_OPEN
    return Tier.NONE


def _split(minutes: int) -> tuple[int, int, int]:
    days, rem = divmod(minutes, 24 * 60)
    hours, mins = divmod(rem, 60)
    return days, hours, mins


def format_duration(minutes: int) -> str:
    """Design 10.4: '2d 05h 12m' (>= 24h), '5h 12m' (< 24h), '47m' (< 1h)."""
    if minutes < 0:
        raise ValueError("minutes must be >= 0")
    days, hours, mins = _split(minutes)
    if days:
        return f"{days}d {hours:02d}h {mins:02d}m"
    if hours:
        return f"{hours}h {mins:02d}m"
    return f"{mins}m"


def format_countdown(due_at: datetime, now: datetime) -> str:
    """Countdown text at minute resolution; past due gives 'Overdue by 1h 03m'."""
    due_at = _utc_minute(due_at, "due_at")
    now = _utc_minute(now, "now")
    delta = int((due_at - now).total_seconds() // 60)
    if delta >= 0:
        return format_duration(delta)
    return f"Overdue by {format_duration(-delta)}"


def accessible_duration(minutes: int) -> str:
    """Screen-reader wording, e.g. '5 hours 12 minutes'."""
    days, hours, mins = _split(abs(minutes))
    parts = []
    for n, unit in ((days, "day"), (hours, "hour"), (mins, "minute")):
        if n:
            parts.append(f"{n} {unit}{'s' if n != 1 else ''}")
    return " ".join(parts) or "0 minutes"
