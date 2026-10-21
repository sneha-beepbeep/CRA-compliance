"""Golden file for P3 (zero deadline errors).

`tests/golden/deadlines.csv` is written by hand, one row per case, in a form
legal can read. Each row is checked against the engine; the file is never
generated from the engine.
"""
import csv
from datetime import datetime
from pathlib import Path

import pytest

from apps.art14.deadlines import EventTimes, compute
from apps.art14.localtime import to_local

GOLDEN = Path(__file__).resolve().parent.parent / "golden" / "deadlines.csv"


def u(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def rows():
    with GOLDEN.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def local(dt, tz):
    if dt is None:
        return ""
    loc = to_local(dt, tz)
    return f"{loc:%Y-%m-%d %H:%M} {loc.tzname()}"


def test_golden_file_has_cases():
    ids = [r["case_id"] for r in rows()]
    assert len(ids) >= 20 and len(ids) == len(set(ids))


@pytest.mark.parametrize("row", rows(), ids=lambda r: r["case_id"])
def test_golden_case(row):
    times = EventTimes(
        event_type=row["event_type"], awareness_at=u(row["awareness_utc"]),
        fix_available_at=u(row["fix_available_utc"]),
        early_warning_filed_at=u(row["early_warning_filed_utc"]),
        notification_filed_at=u(row["notification_filed_utc"]),
        final_report_filed_at=u(row["final_report_filed_utc"]),
        stopped=row["closed_not_reportable"] == "yes",
    )
    d = compute(times, now=u(row["as_of_utc"]), month_rule=row["month_rule"])
    tz = row["display_tz"]
    got = {
        "early_warning_due_utc": d.early_warning.due_at, "notification_due_utc": d.notification.due_at,
        "final_report_due_utc": d.final_report.due_at,
    }
    for col, val in got.items():
        assert val == u(row[col]), col
    assert d.early_warning.state.value == row["early_warning_state"]
    assert d.notification.state.value == row["notification_state"]
    assert d.final_report.state.value == row["final_report_state"]
    assert ",".join(w.value for w in d.warnings) == row["warnings"]
    assert local(d.early_warning.due_at, tz) == row["early_warning_due_local"]
    assert local(d.notification.due_at, tz) == row["notification_due_local"]
    assert local(d.final_report.due_at, tz) == row["final_report_due_local"]
