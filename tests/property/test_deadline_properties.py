"""Hypothesis property tests for the deadline engine and local-time handling."""
import calendar
from datetime import datetime, timedelta, timezone

from hypothesis import given, settings
from hypothesis import strategies as st

from apps.art14.deadlines import EventTimes, EventType, MonthRule, State, add_one_month, compute
from apps.art14.localtime import classify, get_zone, to_utc

UTC = timezone.utc
ZONES = ["Europe/Warsaw", "Europe/Berlin", "Europe/Lisbon", "Europe/Helsinki", "Europe/Dublin",
         "America/New_York", "Australia/Lord_Howe", "Asia/Kolkata", "UTC"]

minutes = st.integers(min_value=0, max_value=60 * 24 * 365 * 6)  # 2026..2032
BASE = datetime(2026, 1, 1, tzinfo=UTC)


def at(m):
    return BASE + timedelta(minutes=m)


instants = minutes.map(at)
types = st.sampled_from(list(EventType))
rules = st.sampled_from(list(MonthRule))


@given(instants, types, instants)
def test_exact_24h_and_72h_gaps(aw, et, now):
    d = compute(EventTimes(et, aw), now=now)
    assert d.early_warning.due_at - aw == timedelta(hours=24)
    assert d.notification.due_at - aw == timedelta(hours=72)


@given(instants, st.sampled_from(ZONES))
def test_local_round_trip(utc_dt, tz):
    # UTC -> local -> UTC gives the original (choosing the offset that local carries).
    zone = get_zone(tz)
    local = utc_dt.astimezone(zone)
    off = local.utcoffset()
    back = to_utc(local.date(), local.time(), tz, now=datetime(2100, 1, 1, tzinfo=UTC),
                  offset_choice=off if classify(local.replace(tzinfo=None), zone) == "ambiguous" else None)
    assert back == utc_dt


@given(instants, rules)
def test_clamp_rule(start, rule):
    due = add_one_month(start, rule)
    if rule is MonthRule.DAYS_30:
        assert due - start == timedelta(days=30)
        return
    assert (due.hour, due.minute) == (start.hour, start.minute)
    exp_month = start.month % 12 + 1
    assert due.month == exp_month
    assert due.year == start.year + (1 if start.month == 12 else 0)
    last = calendar.monthrange(due.year, due.month)[1]
    assert due.day == min(start.day, last)
    assert due > start


@given(instants, instants, rules)
def test_due_times_monotonic_in_start(a, b, rule):
    lo, hi = sorted((a, b))
    assert add_one_month(lo, rule) <= add_one_month(hi, rule)
    for et in EventType:
        dl, dh = compute(EventTimes(et, lo), now=lo), compute(EventTimes(et, hi), now=hi)
        assert dl.early_warning.due_at <= dh.early_warning.due_at
        assert dl.notification.due_at <= dh.notification.due_at
    fl = compute(EventTimes(EventType.VULNERABILITY, BASE, fix_available_at=lo), now=lo)
    fh = compute(EventTimes(EventType.VULNERABILITY, BASE, fix_available_at=hi), now=hi)
    assert fl.final_report.due_at <= fh.final_report.due_at


@given(instants, types, st.integers(-5000, 5000), instants)
def test_filed_state_is_met_iff_not_after_due(aw, et, offset, now):
    d0 = compute(EventTimes(et, aw), now=now)
    filed = d0.early_warning.due_at + timedelta(minutes=offset)
    d = compute(EventTimes(et, aw, early_warning_filed_at=filed), now=now)
    assert d.early_warning.state is (State.MET if offset <= 0 else State.LATE)


@given(instants, types, instants)
def test_unfiled_state_is_open_or_overdue(aw, et, now):
    d = compute(EventTimes(et, aw), now=now)
    expected = State.OVERDUE if now > d.early_warning.due_at else State.OPEN
    assert d.early_warning.state is expected


@settings(max_examples=200)
@given(instants, st.integers(-3 * 24 * 60, 3 * 24 * 60), instants)
def test_awareness_edit_shifts_exactly_24h_72h(aw, shift, now):
    a = compute(EventTimes(EventType.SEVERE_INCIDENT, aw, notification_filed_at=aw + timedelta(hours=1)), now=now)
    b = compute(EventTimes(EventType.SEVERE_INCIDENT, aw + timedelta(minutes=shift),
                           notification_filed_at=aw + timedelta(hours=1)), now=now)
    assert b.early_warning.due_at - a.early_warning.due_at == timedelta(minutes=shift)
    assert b.notification.due_at - a.notification.due_at == timedelta(minutes=shift)
    assert b.final_report.due_at == a.final_report.due_at  # runs from the filing, not awareness


@given(st.sampled_from(ZONES), st.datetimes(min_value=datetime(2026, 1, 1), max_value=datetime(2032, 1, 1)))
def test_local_input_never_silently_guesses(tz, naive):
    """Skipped times are rejected, repeated times need a choice, others convert exactly."""
    import pytest
    from apps.art14.localtime import AmbiguousLocalTimeError, NonexistentLocalTimeError
    naive = naive.replace(second=0, microsecond=0)
    zone = get_zone(tz)
    far = datetime(2100, 1, 1, tzinfo=UTC)
    kind = classify(naive, zone)
    if kind == "nonexistent":
        with pytest.raises(NonexistentLocalTimeError):
            to_utc(naive.date(), naive.time(), tz, now=far)
    elif kind == "ambiguous":
        with pytest.raises(AmbiguousLocalTimeError):
            to_utc(naive.date(), naive.time(), tz, now=far)
    else:
        got = to_utc(naive.date(), naive.time(), tz, now=far)
        assert got.astimezone(zone).replace(tzinfo=None) == naive
