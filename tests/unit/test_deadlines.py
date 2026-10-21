"""Unit tests for the authoritative Art. 14 deadline engine."""
from datetime import datetime, timedelta, timezone

import pytest

from apps.art14.deadlines import (
    ClockKind, DeadlineInputError, EventTimes, EventType, MonthRule, State, Tier,
    Warning_, accessible_duration, add_one_month, compute, format_countdown,
    format_duration, preview_change, tier,
)

UTC = timezone.utc


def u(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


AW = u("2026-10-22T06:05Z")


def vuln(**kw):
    return EventTimes(event_type=EventType.VULNERABILITY, awareness_at=kw.pop("aw", AW), **kw)


def severe(**kw):
    return EventTimes(event_type=EventType.SEVERE_INCIDENT, awareness_at=kw.pop("aw", AW), **kw)


class TestClocks:
    def test_24h_and_72h_are_elapsed_hours(self):
        d = compute(vuln(), now=AW)
        assert d.early_warning.due_at == u("2026-10-23T06:05Z")
        assert d.notification.due_at == u("2026-10-25T06:05Z")  # across the 25 Oct DST change

    def test_vulnerability_final_report_starts_at_fix(self):
        d = compute(vuln(fix_available_at=u("2026-10-24T10:00Z")), now=AW)
        assert d.final_report.start_at == u("2026-10-24T10:00Z")
        assert d.final_report.due_at == u("2026-11-07T10:00Z")

    def test_vulnerability_final_report_not_started_without_fix(self):
        d = compute(vuln(), now=AW)
        assert d.final_report.state is State.NOT_STARTED and d.final_report.due_at is None

    def test_severe_final_report_starts_at_notification_filing(self):
        d = compute(severe(notification_filed_at=u("2026-10-24T10:00Z")), now=AW)
        assert d.final_report.due_at == u("2026-11-24T10:00Z")

    def test_severe_ignores_fix_time_for_final_report(self):
        d = compute(severe(fix_available_at=u("2026-10-23T10:00Z")), now=AW)
        assert d.final_report.state is State.NOT_STARTED

    def test_naive_datetimes_rejected(self):
        with pytest.raises(DeadlineInputError):
            compute(EventTimes(EventType.VULNERABILITY, datetime(2026, 10, 22, 6, 5)), now=AW)
        with pytest.raises(DeadlineInputError):
            compute(vuln(), now=datetime(2026, 10, 22))

    def test_unknown_event_type_rejected(self):
        with pytest.raises(ValueError):
            compute(EventTimes("exploit", AW), now=AW)

    def test_seconds_are_truncated_to_the_minute(self):
        d = compute(vuln(aw=u("2026-10-22T06:05:59Z")), now=AW)
        assert d.early_warning.due_at == u("2026-10-23T06:05Z")

    def test_non_utc_input_normalised(self):
        cest = timezone(timedelta(hours=2))
        d = compute(vuln(aw=datetime(2026, 10, 22, 8, 5, tzinfo=cest)), now=AW)
        assert d.early_warning.due_at == u("2026-10-23T06:05Z")
        assert d.early_warning.due_at.tzinfo == UTC


class TestStates:
    due = u("2026-10-23T06:05Z")

    @pytest.mark.parametrize("filed,state", [
        ("2026-10-23T06:05Z", State.MET),       # exactly at due: met
        ("2026-10-23T06:04Z", State.MET),
        ("2026-10-23T06:06Z", State.LATE),      # a minute later: late
        ("2026-10-23T06:05:59Z", State.MET),    # minute resolution
    ])
    def test_filed_states(self, filed, state):
        d = compute(vuln(early_warning_filed_at=u(filed)), now=u("2026-10-30T00:00Z"))
        assert d.early_warning.state is state

    @pytest.mark.parametrize("now,state", [
        ("2026-10-23T06:04Z", State.OPEN),
        ("2026-10-23T06:05Z", State.OPEN),      # at the due minute: not yet passed
        ("2026-10-23T06:05:59Z", State.OPEN),
        ("2026-10-23T06:06Z", State.OVERDUE),
    ])
    def test_unfiled_states(self, now, state):
        assert compute(vuln(), now=u(now)).early_warning.state is state

    def test_stopped_when_closed_not_reportable(self):
        d = compute(vuln(early_warning_filed_at=u("2026-10-22T09:00Z"), stopped=True),
                    now=u("2026-11-30T00:00Z"))
        assert d.early_warning.state is State.MET
        assert d.notification.state is State.STOPPED
        assert d.final_report.state is State.STOPPED
        assert d.next_running() is None

    def test_next_running_is_soonest_unfiled(self):
        d = compute(vuln(early_warning_filed_at=u("2026-10-22T10:00Z")), now=AW)
        assert d.next_running().kind is ClockKind.NOTIFICATION


class TestMonthRule:
    @pytest.mark.parametrize("start,expected", [
        ("2027-01-31T23:30Z", "2027-02-28T23:30Z"),   # not 1 Mar (SQLite's answer was 3 Mar)
        ("2028-01-31T12:00Z", "2028-02-29T12:00Z"),   # leap year
        ("2027-03-31T08:00Z", "2027-04-30T08:00Z"),
        ("2026-12-31T17:45Z", "2027-01-31T17:45Z"),   # year end
        ("2027-02-28T06:00Z", "2027-03-28T06:00Z"),   # no clamp needed
        ("2027-01-15T00:00Z", "2027-02-15T00:00Z"),
    ])
    def test_calendar_clamp_utc(self, start, expected):
        assert add_one_month(u(start), MonthRule.CALENDAR_CLAMP_UTC) == u(expected)

    def test_days_30(self):
        assert add_one_month(u("2027-01-31T23:30Z"), MonthRule.DAYS_30) == u("2027-03-02T23:30Z")

    def test_default_rule_is_calendar_clamp(self):
        d = compute(severe(notification_filed_at=u("2027-01-31T23:30Z"), aw=u("2027-01-30T10:00Z")),
                    now=u("2027-02-01T00:00Z"))
        assert d.final_report.due_at == u("2027-02-28T23:30Z")

    def test_rule_string_accepted(self):
        assert add_one_month(u("2027-01-31T00:00Z"), "days_30") == u("2027-03-02T00:00Z")

    def test_unknown_rule_rejected(self):
        with pytest.raises(ValueError):
            add_one_month(u("2027-01-31T00:00Z"), "lunar")


class TestEditsAndReclassification:
    def test_awareness_edit_moves_24h_and_72h_only(self):
        fix = u("2026-10-24T10:00Z")
        before = vuln(fix_available_at=fix)
        after = vuln(aw=AW - timedelta(hours=1, minutes=30), fix_available_at=fix)
        ch = {c.kind: c for c in preview_change(before, after, now=AW)}
        assert ch[ClockKind.EARLY_WARNING].after.due_at == ch[ClockKind.EARLY_WARNING].before.due_at - timedelta(minutes=90)
        assert ch[ClockKind.NOTIFICATION].after.due_at == ch[ClockKind.NOTIFICATION].before.due_at - timedelta(minutes=90)
        assert not ch[ClockKind.FINAL_REPORT].due_changed

    def test_awareness_edit_can_turn_met_into_late(self):
        filed = u("2026-10-23T06:00Z")
        before = vuln(early_warning_filed_at=filed)
        after = vuln(aw=AW - timedelta(hours=1), early_warning_filed_at=filed)
        ew = preview_change(before, after, now=u("2026-10-24T00:00Z"))[0]
        assert (ew.before.state, ew.after.state) == (State.MET, State.LATE)
        assert ew.state_changed

    def test_severe_awareness_edit_does_not_move_final_report(self):
        nf = u("2026-10-24T10:00Z")
        ch = preview_change(severe(notification_filed_at=nf),
                            severe(aw=AW - timedelta(hours=5), notification_filed_at=nf), now=AW)
        assert not ch[2].due_changed

    def test_reclassify_keeps_24h_72h_and_rebases_final_report(self):
        fix, nf = u("2026-10-24T10:00Z"), u("2026-10-24T12:00Z")
        ch = preview_change(vuln(fix_available_at=fix, notification_filed_at=nf),
                            severe(fix_available_at=fix, notification_filed_at=nf), now=AW)
        assert not ch[0].due_changed and not ch[1].due_changed
        assert ch[2].before.due_at == u("2026-11-07T10:00Z")
        assert ch[2].after.due_at == u("2026-11-24T12:00Z")

    def test_reclassify_to_vulnerability_without_fix_becomes_not_started(self):
        nf = u("2026-10-24T12:00Z")
        ch = preview_change(severe(notification_filed_at=nf), vuln(notification_filed_at=nf), now=AW)
        assert ch[2].before.state is State.OPEN and ch[2].after.state is State.NOT_STARTED


class TestC7:
    def test_fix_before_awareness_warns_and_computes_as_specified(self):
        d = compute(vuln(aw=u("2026-11-10T10:00Z"), fix_available_at=u("2026-11-08T10:00Z")),
                    now=u("2026-11-10T10:00Z"))
        assert Warning_.FIX_BEFORE_AWARENESS in d.warnings
        assert d.final_report.due_at == u("2026-11-22T10:00Z")

    def test_no_warning_for_normal_order(self):
        assert compute(vuln(fix_available_at=AW + timedelta(hours=1)), now=AW).warnings == ()


class TestTier:
    def test_overdue_beats_everything(self):
        d = compute(vuln(), now=u("2026-10-23T07:00Z"))
        assert tier(d) is Tier.OVERDUE

    def test_early_warning_open(self):
        assert tier(compute(vuln(), now=AW)) is Tier.EARLY_WARNING_OPEN

    def test_notification_open_after_ew_filed(self):
        assert tier(compute(vuln(early_warning_filed_at=AW), now=AW)) is Tier.NOTIFICATION_OPEN

    def test_final_report_open(self):
        d = compute(vuln(early_warning_filed_at=AW, notification_filed_at=AW,
                         fix_available_at=AW), now=AW)
        assert tier(d) is Tier.FINAL_REPORT_OPEN

    def test_none_when_all_filed(self):
        d = compute(vuln(early_warning_filed_at=AW, notification_filed_at=AW,
                         fix_available_at=AW, final_report_filed_at=AW), now=AW)
        assert tier(d) is Tier.NONE


class TestCountdownFormat:
    @pytest.mark.parametrize("minutes,text", [
        (0, "0m"), (47, "47m"), (60, "1h 00m"), (312, "5h 12m"), (24 * 60 - 1, "23h 59m"),
        (24 * 60, "1d 00h 00m"), (2 * 1440 + 312, "2d 05h 12m"),
    ])
    def test_format_duration(self, minutes, text):
        assert format_duration(minutes) == text

    def test_countdown_and_overdue(self):
        due = u("2026-10-23T06:05Z")
        assert format_countdown(due, u("2026-10-23T00:53Z")) == "5h 12m"
        assert format_countdown(due, u("2026-10-23T07:08Z")) == "Overdue by 1h 03m"
        assert format_countdown(due, due) == "0m"

    def test_accessible(self):
        assert accessible_duration(312) == "5 hours 12 minutes"
        assert accessible_duration(1441) == "1 day 1 minute"
        assert accessible_duration(0) == "0 minutes"
