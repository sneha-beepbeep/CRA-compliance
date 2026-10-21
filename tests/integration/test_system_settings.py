"""QA-03: audited operator command for global settings."""
import pytest
from django.core.management import CommandError, call_command
from django.test import Client

from apps.audit.models import AuditEvent
from apps.tenancy.models import SystemSetting

pytestmark = pytest.mark.django_db
REASON = "Pentest passed and criticals fixed; CPO approval recorded."


def test_enable_real_events_is_audited_in_every_vendor_trail(world):
    call_command("set_system_setting", "real_events_enabled", "true", operator="A. Operator", reason=REASON)
    assert SystemSetting.get("real_events_enabled") is True
    entries = AuditEvent.objects.filter(action="changed_system_setting")
    assert {str(e.vendor_tenant_id) for e in entries} == {str(world["A"].vendor.id), str(world["B"].vendor.id)}
    e = entries.first()
    assert e.old_value == {"real_events_enabled": None} and e.new_value == {"real_events_enabled": True}
    assert e.actor_name == "Operator: A. Operator" and e.reason == REASON and e.hash


def test_real_events_flag_takes_effect(world):
    from tests.integration.test_flows import aw_fields
    from apps.art14.models import Art14Event
    w = world["A"]
    call_command("set_system_setting", "real_events_enabled", "on", operator="Op", reason=REASON)
    c = Client()
    c.force_login(w.manager)
    c.post("/events/log", {"event_type": "vulnerability", "product": w.product.pk, "assignee": w.manager.pk,
                           "title": "t", "action": "save", "acknowledge_overdue": "1",
                           **aw_fields(d="2026-01-01", t="10:00")})
    assert Art14Event.objects.filter(vendor_tenant=w.vendor, is_drill=False).count() == 2


def test_disclaimer_change_shows_in_footer_and_is_validated(world):
    new = "Information entered by {vendor_legal_name}. Not a determination of compliance."
    call_command("set_system_setting", "disclaimer_template", new, operator="Op", reason=REASON)
    c = Client()
    c.force_login(world["A"].admin)
    assert "Information entered by Alpha Scoring GmbH. Not a determination of compliance." in c.get("/").content.decode()
    for bad in ("No placeholder here at all.", "Bad {other} placeholder {vendor_legal_name}"):
        with pytest.raises(CommandError, match="disclaimer"):
            call_command("set_system_setting", "disclaimer_template", bad, operator="Op", reason=REASON)


@pytest.mark.parametrize("args,kw,msg", [
    (["real_events_enabled", "maybe"], {"operator": "Op", "reason": REASON}, "true or false"),
    (["month_rule", "lunar"], {"operator": "Op", "reason": REASON}, "month_rule"),
    (["real_events_enabled", "true"], {"operator": "", "reason": REASON}, "operator"),
    (["real_events_enabled", "true"], {"operator": "Op", "reason": "too short"}, "reason"),
])
def test_invalid_changes_rejected_and_not_audited(world, args, kw, msg):
    with pytest.raises(CommandError, match=msg):
        call_command("set_system_setting", *args, **kw)
    assert not AuditEvent.objects.filter(action="changed_system_setting").exists()
    assert SystemSetting.get("real_events_enabled") in (None, False)


def test_list(world, capsys):
    call_command("set_system_setting", "--list")
    out = capsys.readouterr().out
    assert "real_events_enabled = None" in out and "month_rule = 'calendar_clamp_utc'" in out
