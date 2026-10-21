"""Local-time input validation and display (design 8.3, 11.1)."""
from datetime import date, datetime, time, timedelta, timezone

import pytest

from apps.art14.localtime import (
    AmbiguousLocalTimeError, FutureTimeError, NonexistentLocalTimeError, OffsetNotValidError,
    UnknownTimeZoneError, classify, dst_note, format_dual, get_zone, to_utc, wall_clock_shift,
)

UTC = timezone.utc
NOW = datetime(2027, 12, 1, tzinfo=UTC)
WAW = "Europe/Warsaw"


def u(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def test_normal_conversion():
    assert to_utc(date(2026, 10, 22), time(8, 5), WAW, now=NOW) == u("2026-10-22T06:05Z")


def test_seconds_dropped():
    assert to_utc(date(2026, 10, 22), time(8, 5, 42), WAW, now=NOW) == u("2026-10-22T06:05Z")


@pytest.mark.parametrize("d,t", [(date(2027, 3, 28), time(2, 30)), (date(2027, 3, 28), time(2, 0)),
                                 (date(2027, 3, 28), time(2, 59))])
def test_skipped_hour_rejected_with_suggestions(d, t):
    with pytest.raises(NonexistentLocalTimeError) as e:
        to_utc(d, t, WAW, now=NOW)
    assert e.value.message == (f"{t:%H:%M} doesn't exist in Europe/Warsaw on 28 Mar 2027 "
                               "(clocks go forward). Enter 01:59 or 03:00 or later.")


@pytest.mark.parametrize("d", [date(2026, 10, 25), date(2027, 10, 31)])
def test_repeated_hour_requires_offset(d):
    with pytest.raises(AmbiguousLocalTimeError) as e:
        to_utc(d, time(2, 30), WAW, now=NOW)
    labels = [(o.abbreviation, o.offset_label) for o in e.value.options]
    assert labels == [("CEST", "+02:00"), ("CET", "+01:00")]
    assert "02:30 CEST (UTC+02:00)" in e.value.message and "02:30 CET (UTC+01:00)" in e.value.message


def test_repeated_hour_with_explicit_offset():
    assert to_utc(date(2026, 10, 25), time(2, 30), WAW, now=NOW, offset_choice="+02:00") == u("2026-10-25T00:30Z")
    assert to_utc(date(2026, 10, 25), time(2, 30), WAW, now=NOW, offset_choice="UTC+01:00") == u("2026-10-25T01:30Z")


def test_wrong_offset_rejected():
    with pytest.raises(OffsetNotValidError):
        to_utc(date(2026, 10, 25), time(2, 30), WAW, now=NOW, offset_choice="+03:00")
    with pytest.raises(OffsetNotValidError):
        to_utc(date(2026, 10, 22), time(8, 5), WAW, now=NOW, offset_choice="+01:00")


def test_future_tolerance_60s():
    now = u("2026-10-22T06:05:30Z")
    assert to_utc(date(2026, 10, 22), time(8, 6), WAW, now=now) == u("2026-10-22T06:06Z")  # +30 s ok
    with pytest.raises(FutureTimeError) as e:
        to_utc(date(2026, 10, 22), time(8, 7), WAW, now=now)  # +90 s
    assert e.value.message == "Awareness time can't be in the future."


def test_unknown_zone():
    with pytest.raises(UnknownTimeZoneError):
        to_utc(date(2026, 10, 22), time(8, 5), "Mars/Olympus", now=NOW)
    with pytest.raises(UnknownTimeZoneError):
        get_zone("../../etc/passwd")


def test_classify():
    z = get_zone(WAW)
    assert classify(datetime(2026, 10, 25, 2, 30), z) == "ambiguous"
    assert classify(datetime(2027, 3, 28, 2, 30), z) == "nonexistent"
    assert classify(datetime(2027, 3, 28, 3, 0), z) == "normal"


def test_format_dual():
    assert format_dual(u("2026-10-22T12:05Z"), WAW) == "Thu 22 Oct 2026, 14:05 CEST · 12:05 UTC"
    assert format_dual(u("2026-10-25T06:05Z"), WAW) == "Sun 25 Oct 2026, 07:05 CET · 06:05 UTC"


def test_dst_note_and_shift():
    start, due = u("2026-10-22T06:05Z"), u("2026-10-25T06:05Z")
    assert wall_clock_shift(start, due, WAW) == timedelta(hours=-1)
    assert dst_note(start, due, WAW).startswith("Shown 1 hour earlier in local time because clocks change on 25 Oct.")
    assert dst_note(u("2027-03-27T12:00Z"), u("2027-03-28T12:00Z"), WAW).startswith("Shown 1 hour later")
    assert dst_note(u("2026-11-02T09:00Z"), u("2026-11-03T09:00Z"), WAW) is None
