"""Local-time input and display for Art. 14 times (design 8.3, 11.1; NFR-4).

Users type a date, a time and an IANA time zone. We store UTC.

* A time more than 60 s after server ``now`` is rejected (FutureTimeError).
* A local time inside a skipped DST hour is rejected (NonexistentLocalTimeError)
  with the nearest valid times to suggest ("Enter 01:59 or 03:00 or later.").
* A local time inside a repeated DST hour needs an explicit UTC offset choice
  (AmbiguousLocalTimeError lists the options). There is no silent default.

Pure Python (zoneinfo); no Django imports.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

UTC = timezone.utc
FUTURE_TOLERANCE = timedelta(seconds=60)


class LocalTimeError(ValueError):
    """Base class; ``message`` is user-facing copy (design 8.3)."""

    message = "Time not valid."

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


class UnknownTimeZoneError(LocalTimeError):
    def __init__(self, tz_name: str):
        self.tz_name = tz_name
        self.message = f"Unknown time zone: {tz_name}."


class FutureTimeError(LocalTimeError):
    def __init__(self, label: str = "Awareness time"):
        self.message = f"{label} can't be in the future."


@dataclass(frozen=True)
class OffsetOption:
    offset: timedelta
    abbreviation: str
    utc: datetime

    @property
    def offset_label(self) -> str:
        return format_offset(self.offset)


class AmbiguousLocalTimeError(LocalTimeError):
    def __init__(self, local: datetime, tz_name: str, options: tuple[OffsetOption, OffsetOption]):
        self.local = local
        self.tz_name = tz_name
        self.options = options
        hhmm = local.strftime("%H:%M")
        choices = " or ".join(f'"{hhmm} {o.abbreviation} (UTC{o.offset_label})"' for o in options)
        self.message = (f"{hhmm} occurs twice in {tz_name} on {local:%-d %b %Y} (clocks go back). "
                        f"Choose {choices}.")


class NonexistentLocalTimeError(LocalTimeError):
    def __init__(self, local: datetime, tz_name: str, before: datetime, after: datetime):
        self.local = local
        self.tz_name = tz_name
        self.last_valid_before = before
        self.first_valid_after = after
        self.message = (f"{local:%H:%M} doesn't exist in {tz_name} on {local:%-d %b %Y} "
                        f"(clocks go forward). Enter {before:%H:%M} or {after:%H:%M} or later.")


class OffsetNotValidError(LocalTimeError):
    def __init__(self, offset: timedelta):
        self.message = f"UTC{format_offset(offset)} is not a valid offset for this time."


def format_offset(offset: timedelta) -> str:
    total = int(offset.total_seconds() // 60)
    sign = "+" if total >= 0 else "-"
    h, m = divmod(abs(total), 60)
    return f"{sign}{h:02d}:{m:02d}"


def parse_offset(text: str) -> timedelta:
    text = text.strip().upper().removeprefix("UTC")
    sign = -1 if text.startswith("-") else 1
    h, m = text.lstrip("+-").split(":")
    return sign * timedelta(hours=int(h), minutes=int(m))


def get_zone(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        raise UnknownTimeZoneError(tz_name) from None


def _roundtrips(naive: datetime, zone: ZoneInfo, fold: int) -> bool:
    aware = naive.replace(tzinfo=zone, fold=fold)
    back = aware.astimezone(UTC).astimezone(zone)
    return back.replace(tzinfo=None) == naive


def classify(naive: datetime, zone: ZoneInfo) -> str:
    """'normal', 'ambiguous' (repeated hour) or 'nonexistent' (skipped hour)."""
    ok0, ok1 = _roundtrips(naive, zone, 0), _roundtrips(naive, zone, 1)
    if not ok0 and not ok1:
        return "nonexistent"
    off0 = naive.replace(tzinfo=zone, fold=0).utcoffset()
    off1 = naive.replace(tzinfo=zone, fold=1).utcoffset()
    if ok0 and ok1 and off0 != off1:
        return "ambiguous"
    return "normal"


def to_utc(local_date: date, local_time: time, tz_name: str, *, now: datetime,
           offset_choice: str | timedelta | None = None, label: str = "Awareness time") -> datetime:
    """Convert a user-entered local time to UTC (minute resolution), validating it."""
    zone = get_zone(tz_name)
    naive = datetime.combine(local_date, local_time.replace(second=0, microsecond=0))
    kind = classify(naive, zone)

    if kind == "nonexistent":
        before = naive
        while classify(before, zone) == "nonexistent":
            before -= timedelta(minutes=1)
        after = naive
        while classify(after, zone) == "nonexistent":
            after += timedelta(minutes=1)
        raise NonexistentLocalTimeError(naive, tz_name, before, after)

    if kind == "ambiguous":
        opts = []
        for fold in (0, 1):
            aware = naive.replace(tzinfo=zone, fold=fold)
            opts.append(OffsetOption(aware.utcoffset(), aware.tzname(), aware.astimezone(UTC)))
        options = tuple(opts)
        if offset_choice is None:
            raise AmbiguousLocalTimeError(naive, tz_name, options)
        wanted = parse_offset(offset_choice) if isinstance(offset_choice, str) else offset_choice
        match = [o for o in options if o.offset == wanted]
        if not match:
            raise OffsetNotValidError(wanted)
        result = match[0].utc
    else:
        aware = naive.replace(tzinfo=zone, fold=0)
        if offset_choice is not None:
            wanted = parse_offset(offset_choice) if isinstance(offset_choice, str) else offset_choice
            if aware.utcoffset() != wanted:
                raise OffsetNotValidError(wanted)
        result = aware.astimezone(UTC)

    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if result > now + FUTURE_TOLERANCE:
        raise FutureTimeError(label)
    return result


def to_local(utc_dt: datetime, tz_name: str) -> datetime:
    return utc_dt.astimezone(get_zone(tz_name))


def format_dual(utc_dt: datetime, tz_name: str, *, with_weekday: bool = True,
                with_year: bool = True) -> str:
    """'Thu 22 Oct 2026, 14:05 CEST · 12:05 UTC' (design 11.1, 24-hour clock)."""
    local = to_local(utc_dt, tz_name)
    u = utc_dt.astimezone(UTC)
    day_fmt = ("%a " if with_weekday else "") + "%-d %b" + (" %Y" if with_year else "")
    return f"{local.strftime(day_fmt)}, {local:%H:%M} {local.tzname()} · {u:%H:%M} UTC"


def wall_clock_shift(start_utc: datetime, due_utc: datetime, tz_name: str) -> timedelta:
    """How far the local wall-clock time of ``due`` differs from ``start``.

    Non-zero when a DST change falls inside an elapsed-hours window; the UI then
    explains "Shown 1 hour earlier in local time because clocks change on ...".
    """
    zone = get_zone(tz_name)
    return due_utc.astimezone(zone).utcoffset() - start_utc.astimezone(zone).utcoffset()


def dst_note(start_utc: datetime, due_utc: datetime, tz_name: str) -> str | None:
    shift = wall_clock_shift(start_utc, due_utc, tz_name)
    if not shift:
        return None
    zone = get_zone(tz_name)
    # find the local date of the change
    t = start_utc
    off = t.astimezone(zone).utcoffset()
    step = timedelta(hours=1)
    while t < due_utc and t.astimezone(zone).utcoffset() == off:
        t += step
    hours = abs(int(shift.total_seconds() // 3600))
    direction = "earlier" if shift < timedelta(0) else "later"
    unit = "hour" if hours == 1 else "hours"
    return (f"Shown {hours} {unit} {direction} in local time because clocks change on "
            f"{t.astimezone(zone):%-d %b}. The deadline is exactly the stated number of elapsed hours.")


def common_zones() -> list[str]:
    return sorted(z for z in available_timezones() if "/" in z and not z.startswith("Etc/"))
