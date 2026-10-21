"""Differential test: Python engine (authoritative) vs the Postgres cra_deadline_check view."""
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from django.db import connection
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from apps.art14 import deadlines as engine
from apps.art14.models import Art14Event
from apps.tenancy.models import SystemSetting

pytestmark = pytest.mark.django_db
UTC = timezone.utc
GOLDEN = Path(__file__).resolve().parent.parent / "golden" / "deadlines.csv"


def u(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def insert(w, n, *, event_type, aw, fix=None, ew=None, nt=None, fr=None, stopped=False):
    return Art14Event.objects.create(
        vendor_tenant=w.vendor, ref_number=n, event_type=event_type, awareness_at=aw, product=w.product,
        assigned_responder=w.manager, started_by=w.manager, started_via="log_event", started_at=aw,
        fix_available_at=fix, early_warning_filed_at=ew, notification_filed_at=nt, final_report_filed_at=fr,
        status="closed_not_reportable" if stopped else "open", closed_at=aw if stopped else None,
        close_rationale="Determined not reportable in testing." if stopped else "")


def sql_rows(as_of):
    with connection.cursor() as c:
        c.execute("""SELECT event_id, early_warning_due, early_warning_state, notification_due, notification_state,
                            final_report_due, final_report_state FROM cra_deadline_check_at(%s)""", [as_of])
        return {str(r[0]): r[1:] for r in c.fetchall()}


def py_row(ev, as_of, rule):
    d = engine.compute(ev.times(), as_of, rule)
    return (d.early_warning.due_at, d.early_warning.state.value, d.notification.due_at, d.notification.state.value,
            d.final_report.due_at, d.final_report.state.value)


def set_rule(rule):
    SystemSetting.objects.update_or_create(key="month_rule", defaults={"value": rule})


def golden():
    with GOLDEN.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.mark.parametrize("row", golden(), ids=lambda r: r["case_id"])
def test_view_matches_golden_file(world, row):
    set_rule(row["month_rule"])
    w = world["A"]
    ev = insert(w, 100, event_type=row["event_type"], aw=u(row["awareness_utc"]), fix=u(row["fix_available_utc"]),
                ew=u(row["early_warning_filed_utc"]), nt=u(row["notification_filed_utc"]),
                fr=u(row["final_report_filed_utc"]), stopped=row["closed_not_reportable"] == "yes")
    got = sql_rows(u(row["as_of_utc"]))[str(ev.pk)]
    assert got == (u(row["early_warning_due_utc"]), row["early_warning_state"], u(row["notification_due_utc"]),
                   row["notification_state"], u(row["final_report_due_utc"]), row["final_report_state"])


def test_view_respects_session_time_zone(world):
    """Day arithmetic is done in UTC even if the session zone is Europe/Warsaw (DST)."""
    w = world["A"]
    ev = insert(w, 100, event_type="vulnerability", aw=u("2026-10-20T10:00Z"), fix=u("2026-10-20T10:00Z"))
    with connection.cursor() as c:
        c.execute("SET LOCAL TIME ZONE 'Europe/Warsaw'")
        # Compare as UTC text: Django's loader assumes the session zone it configured.
        c.execute("""SELECT to_char(final_report_due AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI'),
                            to_char(notification_due AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI')
                     FROM cra_deadline_check_at('2026-10-21T00:00Z') WHERE event_id = %s""", [str(ev.pk)])
        fr, nt = c.fetchone()
        c.execute("SET LOCAL TIME ZONE 'UTC'")
    assert fr == "2026-11-03 10:00"  # 14 x 24 h across the 25 Oct change, not 337 h
    assert nt == "2026-10-23 10:00"


minute = st.integers(min_value=0, max_value=60 * 24 * 365 * 3).map(lambda m: datetime(2026, 9, 11, tzinfo=UTC) + timedelta(minutes=m))
gap = st.one_of(st.none(), st.integers(min_value=0, max_value=60 * 24 * 40))


@settings(max_examples=60, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(et=st.sampled_from(["vulnerability", "severe_incident"]), aw=minute, fix=st.one_of(st.none(), st.integers(-3000, 30000)),
       ew=gap, nt=gap, fr=gap, stopped=st.booleans(), as_of_off=st.integers(-1000, 60 * 24 * 70),
       rule=st.sampled_from(["calendar_clamp_utc", "days_30"]))
def test_view_matches_engine_property(world, et, aw, fix, ew, nt, fr, stopped, as_of_off, rule):
    set_rule(rule)
    w = world["A"]
    m = lambda off: aw + timedelta(minutes=off) if off is not None else None  # noqa: E731
    ev = insert(w, 1000 + Art14Event.objects.count(), event_type=et, aw=aw, fix=m(fix), ew=m(ew), nt=m(nt),
                fr=m(fr), stopped=stopped)
    as_of = aw + timedelta(minutes=as_of_off)
    assert sql_rows(as_of)[str(ev.pk)] == py_row(ev, as_of, rule)
