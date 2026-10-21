"""Audit rendering: incident masking (design 13) and customer anonymisation (D9, 9.6.5)."""
from types import SimpleNamespace as NS

from apps.audit.render import MASK, render
from apps.tenancy.context import TenantContext

CUST = "c-1"


def entry(**kw):
    base = dict(seq=1, created_at=None, actor_id="u-starter", actor_tenant_id="v-1", actor_name="Lena Braun",
                actor_role="vendor_admin", shared_as="", action="edited_awareness_time", target_label="E-0007",
                old_value={"awareness_at": "2026-10-22T06:05Z"}, new_value={"awareness_at": "2026-10-22T04:35Z"},
                reason="Reason text", is_incident_detail=True)
    base.update(kw)
    return NS(**base)


ADMIN = TenantContext("u-admin", "v-1", "v-1", "vendor", False, False)
RESP = TenantContext("u-resp", "v-1", "v-1", "vendor", True, False)
STARTER = TenantContext("u-starter", "v-1", "v-1", "vendor", False, False)


def test_incident_values_masked_for_non_responders():
    r = render(entry(), ADMIN)
    assert r.old == MASK and r.new == MASK and r.reason == MASK and r.masked
    assert r.action == "edited_awareness_time"  # that it happened is still shown


def test_responders_see_values():
    r = render(entry(), RESP)
    assert r.new == {"awareness_at": "2026-10-22T04:35Z"} and r.reason == "Reason text"


def test_starter_sees_own_started_clock_entry_only():
    assert not render(entry(action="started_clock"), STARTER).masked
    assert render(entry(action="edited_awareness_time"), STARTER).masked
    assert render(entry(action="started_clock", actor_id="someone-else"), STARTER).masked


def test_non_incident_entries_never_masked():
    assert not render(entry(is_incident_detail=False), ADMIN).masked


def cust(shared_as):
    return entry(actor_role="customer_admin", actor_tenant_id=CUST, actor_name="Jan Schmidt", shared_as=shared_as,
                 is_incident_detail=False, action="exported_pdf")


NAMES = {CUST: "Bank A"}


def test_named_only_when_entry_and_current_setting_are_named():
    assert render(cust("named"), ADMIN, current_modes={CUST: "named"}, customer_names=NAMES).who == "Jan Schmidt (Bank A)"


def test_named_to_organisation_applies_retroactively():
    r = render(cust("named"), ADMIN, current_modes={CUST: "organisation"}, customer_names=NAMES)
    assert r.who == "Bank A user" and "organisation only" in r.note


def test_organisation_to_named_applies_forward_only():
    r = render(cust("organisation"), ADMIN, current_modes={CUST: "named"}, customer_names=NAMES)
    assert r.who == "Bank A user"


def test_default_is_organisation_only():
    assert render(cust("named"), RESP, customer_names=NAMES).who == "Bank A user"


def test_no_stable_pseudonym():
    """Two different customer users render identically under organisation-only (9.6.2)."""
    a = render(cust("organisation"), ADMIN, customer_names=NAMES)
    other = entry(actor_role="customer_admin", actor_tenant_id=CUST, actor_id="other", actor_name="Eva Weber",
                  shared_as="organisation", is_incident_detail=False)
    b = render(other, ADMIN, customer_names=NAMES)
    assert a.who == b.who == "Bank A user"


# QA-08: readable actions and values
from apps.audit.render import action_label, readable  # noqa: E402


def test_action_labels():
    assert action_label("edited_awareness_time") == "Edit awareness time"
    assert action_label("something_new") == "Something new"


def test_readable_values_show_local_and_utc():
    txt = readable({"awareness_at": "2026-10-22T06:05:00Z", "review_by": "2027-06-30", "status": "evidence_attached"},
                   "Europe/Warsaw")
    assert txt == ("Awareness time: Thu 22 Oct 2026, 08:05 CEST · 06:05 UTC; Review by: 2027-06-30; "
                   "Status: evidence attached")
    assert readable(MASK, "UTC") == MASK and readable(None, "UTC") == ""


def test_rendered_entry_masks_readable_text():
    r = render(entry(), ADMIN, tz="Europe/Warsaw")
    assert r.old_text == MASK and r.new_text == MASK and r.action_label == "Edit awareness time"
    r = render(entry(), RESP, tz="Europe/Warsaw")
    assert "06:35 CEST · 04:35 UTC" in r.new_text


def test_drill_outcome_notes_masked_for_non_responders():
    e = entry(action="recorded_drill_outcome", new_value={"early_warning_would_be_met": "yes", "notes": "free text"})
    assert render(e, ADMIN).new == MASK
