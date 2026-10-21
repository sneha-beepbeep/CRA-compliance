"""Phase 1a flows over HTTP, against real Postgres with RLS active."""
from datetime import date, datetime, timedelta, timezone

import pytest
from django.test import Client

from apps.airisks.models import AIRisk
from apps.art14.models import Art14Event
from apps.audit.models import AuditEvent
from apps.catalog.models import Taxonomy
from apps.core import clock
from apps.requirements.models import RequirementStatus
from apps.tenancy.models import RoleGrant, SystemSetting, Tenant

pytestmark = pytest.mark.django_db
UTC = timezone.utc
NOW = datetime(2026, 10, 22, 12, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def frozen(monkeypatch):
    monkeypatch.setattr(clock, "now", lambda: NOW)


def client_for(user):
    c = Client()
    c.force_login(user)
    return c


def aw_fields(d="2026-10-22", t="08:05", tz="Europe/Warsaw", **extra):
    return {"awareness_date": d, "awareness_time": t, "awareness_tz": tz, **extra}


def log_drill(c, w, **kw):
    data = {"event_type": "vulnerability", "product": w.product.pk, "assignee": w.manager.pk, "title": "Drill title",
            "action": "save", "drill": "1", **aw_fields(), **kw}
    return c.post("/events/log?drill=1", data)


def latest(w):
    return Art14Event.objects.filter(vendor_tenant=w.vendor).order_by("-ref_number").first()


def time_post(c, ev, which, d, t, tz="UTC", reason=""):
    return c.post(f"/events/{ev.pk}/time", {
        "which_prefix": which, f"{which}-which": which, f"{which}-when_date": d, f"{which}-when_time": t,
        f"{which}-when_tz": tz, f"{which}-reason": reason, f"{which}-row_version": Art14Event.objects.get(pk=ev.pk).row_version})


class TestDrillFlow:
    def test_log_strip_filings_close_reopen(self, world):
        w = world["A"]
        c = client_for(w.manager)
        r = log_drill(c, w)
        assert r.status_code == 302
        ev = latest(w)
        assert ev.is_drill and ev.ref == "E-0003" and ev.awareness_at == datetime(2026, 10, 22, 6, 5, tzinfo=UTC)
        assert ev.detail.title == "Drill title"
        strip = c.get("/clocks/strip").content.decode()
        assert "DRILL E-0003" in strip
        assert time_post(c, ev, "early_warning", "2026-10-22", "10:00").status_code == 302
        assert time_post(c, ev, "notification", "2026-10-22", "11:00").status_code == 302
        assert time_post(c, ev, "fix", "2026-10-22", "11:30").status_code == 302
        assert time_post(c, ev, "final_report", "2026-10-22", "11:45").status_code == 302
        ev.refresh_from_db()
        assert ev.early_warning_filed_at == datetime(2026, 10, 22, 10, 0, tzinfo=UTC)
        r = c.post(f"/events/{ev.pk}/close", {"outcome": "closed_reporting_complete", "row_version": ev.row_version})
        assert r.status_code == 302
        ev.refresh_from_db()
        assert ev.status == "closed_reporting_complete"
        assert "DRILL E-0003" not in c.get("/clocks/strip").content.decode()
        r = c.post(f"/events/{ev.pk}/reopen", {"reason": "short", "row_version": ev.row_version})
        assert r.status_code == 400
        r = c.post(f"/events/{ev.pk}/reopen", {"reason": "Reopened to correct a filing time in the drill.",
                                               "row_version": ev.row_version})
        assert r.status_code == 302 and Art14Event.objects.get(pk=ev.pk).status == "open"
        actions = list(AuditEvent.objects.filter(target_id=str(ev.pk)).values_list("action", flat=True))
        for a in ("logged_event", "recorded_early_warning", "recorded_fix", "closed_event", "reopened_event"):
            assert a in actions

    def test_drill_outcome(self, world):
        w = world["A"]
        c = client_for(w.manager)
        log_drill(c, w)
        ev = latest(w)
        c.post(f"/events/{ev.pk}/drill-outcome", {"answer": "yes", "notes": "On time."})
        assert ev.drill_outcome.early_warning_would_be_met == "yes"

    def test_filing_before_awareness_and_future_rejected(self, world):
        w = world["A"]
        c = client_for(w.manager)
        log_drill(c, w)
        ev = latest(w)
        assert time_post(c, ev, "early_warning", "2026-10-22", "06:00").status_code == 400
        assert time_post(c, ev, "early_warning", "2026-10-22", "12:05").status_code == 400
        assert Art14Event.objects.get(pk=ev.pk).early_warning_filed_at is None

    def test_correcting_a_filing_needs_a_reason(self, world):
        w = world["A"]
        c = client_for(w.manager)
        log_drill(c, w)
        ev = latest(w)
        time_post(c, ev, "early_warning", "2026-10-22", "10:00")
        assert time_post(c, ev, "early_warning", "2026-10-22", "10:30").status_code == 400
        assert time_post(c, ev, "early_warning", "2026-10-22", "10:30",
                         reason="Typo in the first entry, checked the platform receipt.").status_code == 302


class TestC6DrillsOnly:
    def test_real_events_blocked_until_enabled(self, world):
        w = world["A"]
        c = client_for(w.manager)
        assert "+ Log event" not in c.get("/events/").content.decode()
        data = {"event_type": "vulnerability", "product": w.product.pk, "assignee": w.manager.pk, "title": "x",
                "action": "save", **aw_fields()}
        c.post("/events/log", data)
        assert latest(w).is_drill  # forced to a drill
        SystemSetting.objects.create(key="real_events_enabled", value=True)
        c.post("/events/log", data)
        assert not latest(w).is_drill


class TestStartClock:
    def form(self, w, **kw):
        return {"event_type": "vulnerability", "product": w.product.pk, "assignee": w.manager.pk, "action": "save",
                **aw_fields(t="13:47"), **kw}

    def test_admin_starts_clock_then_responder_takes_it(self, world):
        w = world["A"]
        admin = client_for(w.admin)
        page = admin.get("/events/start").content.decode()
        assert "<textarea" not in page  # no free text at all (OQ-D4)
        r = admin.post("/events/start", self.form(w))
        ev = latest(w)
        assert r["Location"] == f"/events/{ev.pk}/started/"
        assert ev.awaiting_responder and ev.started_via == "start_clock" and ev.is_drill  # C6 forces drill
        conf = admin.get(r["Location"]).content.decode()
        assert "The dashboard does not notify them." in conf and ev.ref in conf
        assert admin.get(r["Location"]).status_code == 404  # shown once
        assert "AWAITING RESPONDER" in admin.get("/clocks/strip").content.decode()
        responder = client_for(w.manager)
        responder.get(f"/events/{ev.pk}/")
        ev.refresh_from_db()
        assert not ev.awaiting_responder
        assert "Details restricted to incident responders" in admin.get(f"/events/{ev.pk}/").content.decode()

    def test_extra_detail_fields_are_ignored(self, world):
        w = world["A"]
        admin = client_for(w.admin)
        admin.post("/events/start", self.form(w, title="should not be stored", description="nope"))
        ev = latest(w)
        assert not hasattr(ev, "detail") or not ev.detail.title

    def test_blocked_without_a_responder(self, world):
        w = world["A"]
        RoleGrant.objects.filter(vendor_tenant=w.vendor).update(revoked_at=NOW)
        r = client_for(w.admin).get("/events/start")
        assert r.status_code == 409 and "No incident responder exists" in r.content.decode()
        assert "No incident responder assigned. Clocks can&#x27;t be routed." in \
            client_for(w.admin).get("/clocks/strip").content.decode()

    def test_reassign_by_any_admin(self, world):
        w = world["A"]
        RoleGrant.objects.create(vendor_tenant=w.vendor, user=w.admin, role="incident_responder", granted_at=NOW)
        r = client_for(w.admin).post(f"/events/{w.drill.pk}/reassign", {"assignee": w.admin.pk})
        assert r.status_code == 302
        w.drill.refresh_from_db()
        assert w.drill.assigned_responder_id == w.admin.pk


class TestLocalTimeInput:
    def test_ambiguous_hour_requires_choice(self, world, monkeypatch):
        monkeypatch.setattr(clock, "now", lambda: datetime(2026, 10, 26, tzinfo=UTC))
        w = world["A"]
        c = client_for(w.manager)
        r = log_drill(c, w, awareness_date="2026-10-25", awareness_time="02:30")
        body = r.content.decode()
        assert r.status_code == 200 and "occurs twice" in body and "02:30 CET (UTC+01:00)" in body
        r = log_drill(c, w, awareness_date="2026-10-25", awareness_time="02:30", awareness_offset="+01:00")
        assert r.status_code == 302 and latest(w).awareness_at == datetime(2026, 10, 25, 1, 30, tzinfo=UTC)

    def test_skipped_hour_rejected(self, world, monkeypatch):
        monkeypatch.setattr(clock, "now", lambda: datetime(2027, 3, 29, tzinfo=UTC))
        w = world["A"]
        r = log_drill(client_for(w.manager), w, awareness_date="2027-03-28", awareness_time="02:30")
        assert "Enter 01:59 or 03:00 or later." in r.content.decode()

    def test_future_rejected_and_old_warns(self, world):
        w = world["A"]
        c = client_for(w.manager)
        r = log_drill(c, w, awareness_time="14:02")  # 12:02 UTC, > 60 s after 12:00
        assert "Awareness time can&#x27;t be in the future." in r.content.decode()
        r = c.post("/events/log?drill=1", {"event_type": "vulnerability", "product": w.product.pk,
                                           "assignee": w.manager.pk, "title": "t", "drill": "1",
                                           **aw_fields(d="2026-10-20")})
        assert "already passed" in r.content.decode()

    def test_preview_shows_dst_note(self, world):
        w = world["A"]
        r = client_for(w.manager).post("/events/log?drill=1", {"event_type": "vulnerability", "product": w.product.pk,
                                                               "assignee": w.manager.pk, "title": "t", "drill": "1",
                                                               **aw_fields()})
        body = r.content.decode()
        assert "Fri 23 Oct 2026, 08:05 CEST · 06:05 UTC" in body
        assert "Sun 25 Oct 2026, 07:05 CET · 06:05 UTC" in body
        assert "Shown 1 hour earlier in local time because clocks change on 25 Oct." in body


class TestAwarenessEdit:
    def test_preview_confirm_and_masking(self, world):
        w = world["A"]
        c = client_for(w.manager)
        log_drill(c, w)
        ev = latest(w)
        # Moving awareness a day earlier turns the open early warning into overdue (now = 22 Oct 12:00 UTC).
        data = {**aw_fields(d="2026-10-21", t="13:00"), "reason": "Logs show we knew a day earlier than first thought.",
                "row_version": Art14Event.objects.get(pk=ev.pk).row_version}
        r = c.post(f"/events/{ev.pk}/awareness", {**data, "action": "preview"})
        body = r.content.decode()
        assert "Before and after" in body and "Early warning will change from open to overdue." in body
        assert Art14Event.objects.get(pk=ev.pk).awareness_edit_count == 0  # preview changes nothing
        r = c.post(f"/events/{ev.pk}/awareness", {**data, "action": "confirm"})
        assert r.status_code == 302
        ev.refresh_from_db()
        assert ev.awareness_at == datetime(2026, 10, 21, 11, 0, tzinfo=UTC) and ev.awareness_edit_count == 1
        responder_audit = c.get("/audit/?action=edited_awareness_time").content.decode()
        admin_audit = client_for(w.admin).get("/audit/?action=edited_awareness_time").content.decode()
        assert "2026-10-21T11:00:00Z" in responder_audit and "a day earlier" in responder_audit
        assert "2026-10-21T11:00:00Z" not in admin_audit and "a day earlier" not in admin_audit
        assert "Deadlines recalculated by a responder" in client_for(w.admin).get(f"/events/{ev.pk}/").content.decode()
        assert "[value hidden: responders only]" in admin_audit

    def test_stale_row_version_conflicts(self, world):
        w = world["A"]
        c = client_for(w.manager)
        log_drill(c, w)
        ev = latest(w)
        data = {**aw_fields(t="07:00"), "reason": "A reason that is long enough to pass.", "row_version": 99,
                "action": "confirm"}
        r = c.post(f"/events/{ev.pk}/awareness", data)
        assert "changed by someone else" in r.content.decode()


class TestRequirements:
    def test_status_rules_summary_and_staleness(self, world):
        w = world["A"]
        c = client_for(w.admin)
        s = w.status
        r = c.post(f"/requirements/{s.pk}/", {"status": "evidence_attached", "row_version": 0})
        assert "Add at least one evidence item first." in r.content.decode()
        c.post(f"/requirements/{s.pk}/evidence", {"title": "Threat model v3", "type": "document",
                                                  "evidence_date": "2026-10-01", "url": "https://intranet.example/tm"})
        r = c.post(f"/requirements/{s.pk}/", {"status": "evidence_attached", "row_version": 0})
        assert "A review-by date is required." in r.content.decode()
        r = c.post(f"/requirements/{s.pk}/", {"status": "evidence_attached", "review_by": "2027-06-30", "row_version": 0})
        assert r.status_code == 302
        page = c.get("/requirements/").content.decode()
        assert "Evidence attached for 1 of 27 requirements." in page
        assert "This is a count of records entered here. It is not a score." in page
        RequirementStatus.objects.filter(pk=s.pk).update(review_by=date(2026, 10, 1))
        page = c.get("/requirements/").content.decode()
        assert "evidence stale" in page and "date passed" in page
        assert "Review dates passed (1)" in c.get("/").content.decode()

    def test_not_applicable_needs_20_char_rationale(self, world):
        w = world["A"]
        c = client_for(w.admin)
        r = c.post(f"/requirements/{w.status.pk}/", {"status": "not_applicable", "rationale": "too short", "row_version": 0})
        assert r.status_code == 400
        r = c.post(f"/requirements/{w.status.pk}/", {"status": "not_applicable", "row_version": 0,
                                                     "rationale": "The product has no network interface at all."})
        assert r.status_code == 302

    def test_stale_cannot_be_chosen(self, world):
        w = world["A"]
        r = client_for(w.admin).post(f"/requirements/{w.status.pk}/", {"status": "evidence_stale", "row_version": 0})
        assert r.status_code == 400


class TestAIRisks:
    def test_seeding_waits_for_licence(self, world):
        w = world["A"]
        c = client_for(w.admin)
        c.post("/ai-risks/seed", {"taxonomy": "mitre_atlas"})
        assert AIRisk.objects.filter(version=w.version).count() == 1
        Taxonomy.objects.filter(code="mitre_atlas").update(licence_status="cleared")
        c.post("/ai-risks/seed", {"taxonomy": "mitre_atlas"})
        seeded = AIRisk.objects.filter(version=w.version, taxonomy_item__isnull=False)
        assert seeded.count() == 3 and set(seeded.values_list("stage", flat=True)) == {"not_assessed"}

    def test_stage_rules_and_last_tested(self, world):
        w = world["A"]
        c = client_for(w.admin)
        r = c.post(f"/ai-risks/{w.risk.pk}/", {"stage": "accepted", "row_version": 0})
        assert r.status_code == 400
        c.post(f"/ai-risks/{w.risk.pk}/evidence", {"title": "Red-team report", "type": "test_report",
                                                   "evidence_date": "2026-09-12"})
        r = c.post(f"/ai-risks/{w.risk.pk}/", {"stage": "treatment_in_place", "review_by": "2027-03-01",
                                               "row_version": 0, "owner": w.admin.pk})
        assert r.status_code == 302
        page = c.get("/ai-risks/").content.decode()
        assert "12 Sep 2026" in page and "treatment in place – evidence attached" in page
        assert "It is not a robustness rating." in page


class TestRegistryAndRoles:
    def test_unsupported_category_rejected_and_version_attaches_sets(self, world):
        w = world["A"]
        c = client_for(w.admin)
        r = c.post("/setup/product", {"name": "Insurer", "intended_purpose": "Pricing", "category": "5(c)"})
        assert r.status_code == 400
        c.post("/setup/product", {"name": "Second", "intended_purpose": "Scoring", "category": "5(b)",
                                  "delivery_model": "hosted_only"})
        from apps.registry.models import Product
        p = Product.objects.get(name="Second")
        c.post("/setup/version", {"product": p.pk, "label": "1.0"})
        assert RequirementStatus.objects.filter(version__product=p).count() == 27
        c.post("/setup/deployment", {"customer_name": "New Lender", "label": "New Lender – prod",
                                     "version": p.versions.first().pk})
        t = Tenant.objects.get(display_name="New Lender")
        assert t.kind == "customer" and t.vendor_tenant_id == w.vendor.pk and t.activity_sharing.mode == "organisation"

    def test_only_access_managers_grant_responder(self, world):
        w = world["A"]
        assert client_for(w.admin).post(f"/setup/users/{w.admin.pk}/responder", {"grant": "1"}).status_code == 404
        assert client_for(w.manager).post(f"/setup/users/{w.admin.pk}/responder", {"grant": "1"}).status_code == 302
        assert RoleGrant.objects.filter(user=w.admin, revoked_at__isnull=True).exists()
        assert AuditEvent.objects.filter(action="granted_responder").exists()



class TestSetupChecklist:
    """Deviation 13: "Invite a customer admin" is optional, hidden until invitations exist."""

    def ctx_request(self, w, user):
        from types import SimpleNamespace as NS

        from apps.tenancy.context import resolve
        return NS(tenant_ctx=resolve(user), user=user)

    def test_complete_with_step_hidden(self, world):
        from apps.registry.services import setup_checklist
        w = world["A"]
        cl = setup_checklist(self.ctx_request(w, w.manager))
        assert cl.optional == [] and cl.complete and (cl.done_count, cl.total) == (6, 6)
        assert all("Invite" not in s.label for s in cl.required)
        c = client_for(w.manager)
        assert "Setup:" not in c.get("/").content.decode()  # panel gone once complete
        setup = c.get("/setup/").content.decode()
        assert "Invite a customer admin" not in setup and "Optional steps" not in setup

    def test_optional_step_never_affects_count(self, world, settings):
        from apps.registry.services import setup_checklist
        from apps.tenancy.models import CustomerInvitation
        settings.CUSTOMER_INVITATIONS_ENABLED = True
        w = world["A"]
        cl = setup_checklist(self.ctx_request(w, w.manager))
        assert [s.label for s in cl.optional] == ["Invite a customer admin"] and not cl.optional[0].done
        assert cl.complete and (cl.done_count, cl.total) == (6, 6)
        CustomerInvitation.objects.create(vendor_tenant=w.vendor, customer_tenant=w.customer, email="x@c.example",
                                          invited_by=w.manager, invited_at=NOW)
        cl2 = setup_checklist(self.ctx_request(w, w.manager))
        assert cl2.optional[0].done and (cl2.done_count, cl2.total) == (6, 6)
        # an incomplete required step still counts; the optional one still doesn't
        cl3 = setup_checklist(self.ctx_request(w, w.admin))  # admin hasn't confirmed a time zone
        assert (cl3.done_count, cl3.total) == (5, 6) and not cl3.complete

    def test_optional_step_rendered_separately_when_enabled(self, world, settings):
        settings.CUSTOMER_INVITATIONS_ENABLED = True
        w = world["A"]
        body = client_for(w.admin).get("/").content.decode()
        assert "Setup: 5 of 6 steps done." in body
        assert "Optional steps" in body and "Optional: <a" in body and "don't count toward setup" in body
