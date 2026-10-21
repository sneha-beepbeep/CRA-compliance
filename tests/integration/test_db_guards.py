"""Triggers and constraints: audit append-only + hash chain, drill guards, minute truncation."""
from datetime import timedelta

import pytest
from django.db import IntegrityError, InternalError, connection, transaction
from django.db.utils import DatabaseError, ProgrammingError

from apps.art14.models import Art14CustomerReference, Art14Event, Art14UsersInformed
from apps.audit.models import AuditEvent

pytestmark = pytest.mark.django_db


def add_audit(vendor, n=3, **kw):
    for i in range(n):
        AuditEvent.objects.create(vendor_tenant=vendor, actor_name="T", actor_role="vendor_admin", area="t",
                                  action=f"a{i}", new_value={"i": i}, **kw)


def verify(vendor):
    with connection.cursor() as c:
        c.execute("SELECT audit_verify_chain(%s)", [str(vendor.id)])
        return c.fetchone()[0]


def test_hash_chain_is_built_and_verifies(world):
    a = world["A"].vendor
    add_audit(a, 5)
    rows = list(AuditEvent.objects.filter(vendor_tenant=a).order_by("seq"))
    assert rows[0].prev_hash == "" and all(len(r.hash) == 64 for r in rows)
    assert all(rows[i].prev_hash == rows[i - 1].hash for i in range(1, len(rows)))
    assert verify(a) is None


def test_chains_are_per_vendor(world):
    add_audit(world["A"].vendor, 2)
    add_audit(world["B"].vendor, 2)
    first_b = AuditEvent.objects.filter(vendor_tenant=world["B"].vendor).order_by("seq").first()
    assert first_b.prev_hash == ""


def test_client_supplied_hash_and_time_are_ignored(world):
    a = world["A"].vendor
    e = AuditEvent.objects.create(vendor_tenant=a, actor_name="T", actor_role="x", area="t", action="a",
                                  hash="f" * 64, prev_hash="0" * 64)
    e.refresh_from_db()
    assert e.hash != "f" * 64 and e.prev_hash == "" and e.created_at is not None and e.seq is not None


@pytest.mark.parametrize("sql", ["UPDATE audit_event SET action='x'", "DELETE FROM audit_event",
                                 "TRUNCATE audit_event"])
def test_audit_is_append_only_even_for_the_owner(world, sql):
    add_audit(world["A"].vendor, 1)
    with connection.cursor() as c:
        c.execute("SET CONSTRAINTS ALL IMMEDIATE")  # flush deferred FK checks so TRUNCATE reaches the trigger
    with pytest.raises(DatabaseError, match="append-only"), transaction.atomic():
        with connection.cursor() as c:
            c.execute(sql)


@pytest.mark.parametrize("sql", ["UPDATE audit_event SET action='x'", "DELETE FROM audit_event"])
def test_app_role_has_no_update_or_delete_on_audit(world, as_role, sql):
    add_audit(world["A"].vendor, 1)
    with as_role("app_vendor", world["A"].vendor.id) as c:
        with pytest.raises(ProgrammingError, match="permission denied"), transaction.atomic():
            c.execute(sql)


def test_tampering_is_detected_by_the_chain(world):
    a = world["A"].vendor
    add_audit(a, 4)
    target = AuditEvent.objects.filter(vendor_tenant=a).order_by("seq")[2]
    with connection.cursor() as c:
        c.execute("SET CONSTRAINTS ALL IMMEDIATE")
        c.execute("ALTER TABLE audit_event DISABLE TRIGGER audit_event_no_update_delete")
        c.execute("UPDATE audit_event SET reason='rewritten' WHERE id=%s", [str(target.id)])
        c.execute("ALTER TABLE audit_event ENABLE TRIGGER audit_event_no_update_delete")
    assert verify(a) == target.seq


def test_is_drill_cannot_change(world):
    ev = world["A"].drill
    with pytest.raises(DatabaseError, match="is_drill cannot change"), transaction.atomic():
        Art14Event.objects.filter(pk=ev.pk).update(is_drill=False)


def test_ref_number_cannot_change(world):
    with pytest.raises(DatabaseError, match="identity fields"), transaction.atomic():
        Art14Event.objects.filter(pk=world["A"].event.pk).update(ref_number=99)


def _informed(w, ev, released=True):
    return Art14UsersInformed(vendor_tenant=w.vendor, event=ev, deployment=w.deployment, customer_tenant=w.customer,
                              informed_at=ev.awareness_at, released=released, recorded_by=w.manager,
                              recorded_at=ev.awareness_at)


def test_drills_cannot_be_released_or_referenced(world):
    w = world["A"]
    with pytest.raises(DatabaseError, match="drills cannot be released"), transaction.atomic():
        _informed(w, w.drill).save()
    with pytest.raises(DatabaseError, match="drills cannot be released"), transaction.atomic():
        Art14CustomerReference.objects.create(vendor_tenant=w.vendor, event=w.drill, customer_tenant=w.customer,
                                              number=1)
    _informed(w, w.event).save()  # real events can be released


def test_filing_before_awareness_rejected(world):
    ev = world["A"].event
    with pytest.raises(IntegrityError), transaction.atomic():
        Art14Event.objects.filter(pk=ev.pk).update(early_warning_filed_at=ev.awareness_at - timedelta(minutes=1))


def test_times_must_be_minute_truncated(world):
    ev = world["A"].event
    with pytest.raises(IntegrityError), transaction.atomic():
        Art14Event.objects.filter(pk=ev.pk).update(fix_available_at=ev.awareness_at + timedelta(seconds=30))


def test_closed_complete_needs_all_filings(world):
    ev = world["A"].event
    with pytest.raises(IntegrityError), transaction.atomic():
        Art14Event.objects.filter(pk=ev.pk).update(status="closed_reporting_complete", closed_at=ev.awareness_at)


def test_not_reportable_needs_rationale(world):
    ev = world["A"].event
    with pytest.raises(IntegrityError), transaction.atomic():
        Art14Event.objects.filter(pk=ev.pk).update(status="closed_not_reportable", closed_at=ev.awareness_at)


def test_customer_incident_view_non_inference(world, as_role):
    """'No events' and 'only unreleased events' look the same to the customer."""
    a, b = world["A"], world["B"]
    # B's customer: vendor B has events, none released. Remove nothing; compare with a fresh customer of A.
    with as_role("app_customer", b.customer.id, vendor_tenant_id=b.vendor.id) as c:
        c.execute("SELECT * FROM cust_incident")
        only_unreleased = c.fetchall()
    _informed(a, a.event, released=False).save()  # recorded but not released
    with as_role("app_customer", a.customer.id, vendor_tenant_id=a.vendor.id) as c:
        c.execute("SELECT * FROM cust_incident")
        unreleased_row = c.fetchall()
    assert only_unreleased == [] and unreleased_row == []


def test_released_incident_uses_customer_reference(world, as_role):
    a = world["A"]
    _informed(a, a.event).save()
    Art14CustomerReference.objects.create(vendor_tenant=a.vendor, event=a.event, customer_tenant=a.customer, number=1)
    with as_role("app_customer", a.customer.id, vendor_tenant_id=a.vendor.id) as c:
        c.execute("SELECT reference, event_type FROM cust_incident")
        assert c.fetchall() == [("INC-1", "vulnerability")]


# QA-09: vendor sessions can't call the verifier; anchored heads detect tail deletion.
def test_vendor_role_cannot_call_verify(world, as_role):
    with as_role("app_vendor", world["A"].vendor.id) as c:
        with pytest.raises(ProgrammingError, match="permission denied"), transaction.atomic():
            c.execute("SELECT audit_verify_chain(%s)", [str(world["B"].vendor.id)])


def test_anchored_head_detects_tail_deletion(world, tmp_path, capsys):
    import json

    from django.core.management import call_command
    a = world["A"].vendor
    add_audit(a, 3)
    call_command("verify_audit_chain")
    anchors = tmp_path / "anchors.json"
    anchors.write_text(capsys.readouterr().out)
    assert json.loads(anchors.read_text())["problems"] == []
    newest = AuditEvent.objects.filter(vendor_tenant=a).order_by("-seq").first()
    with connection.cursor() as c:
        c.execute("SET CONSTRAINTS ALL IMMEDIATE")
        c.execute("ALTER TABLE audit_event DISABLE TRIGGER audit_event_no_update_delete")
        c.execute("DELETE FROM audit_event WHERE id=%s", [str(newest.id)])
        c.execute("ALTER TABLE audit_event ENABLE TRIGGER audit_event_no_update_delete")
    assert verify(a) is None  # the chain alone can't see it ...
    with pytest.raises(SystemExit) as e:
        call_command("verify_audit_chain", anchors=str(anchors))
    assert e.value.code == 1  # ... the anchor can
    assert "entries removed" in capsys.readouterr().out
