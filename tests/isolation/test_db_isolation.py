"""Tenant isolation enforced by the database (technical plan, "Isolation tests")."""
import pytest
from django.db import connection, transaction
from django.db.utils import ProgrammingError

pytestmark = pytest.mark.django_db


def tenant_tables():
    with connection.cursor() as c:
        c.execute("""SELECT c.table_name FROM information_schema.columns c
                     JOIN information_schema.tables t USING (table_schema, table_name)
                     WHERE c.table_schema='public' AND c.column_name='vendor_tenant_id' AND t.table_type='BASE TABLE'
                     ORDER BY 1""")
        return [r[0] for r in c.fetchall()]


def base_tables():
    with connection.cursor() as c:
        c.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY 1")
        return [r[0] for r in c.fetchall()]


def test_every_tenant_table_has_rls_and_a_vendor_policy():
    tables = tenant_tables()
    assert len(tables) >= 20
    with connection.cursor() as c:
        for t in tables:
            c.execute("SELECT relrowsecurity FROM pg_class WHERE relname=%s", [t])
            assert c.fetchone()[0], f"RLS not enabled on {t}"
            c.execute("SELECT count(*) FROM pg_policies WHERE tablename=%s AND policyname='vendor_isolation'", [t])
            assert c.fetchone()[0] == 1, f"no vendor_isolation policy on {t}"


def test_customer_role_is_denied_every_base_table():
    with connection.cursor() as c:
        for t in base_tables():
            for priv in ("SELECT", "INSERT", "UPDATE", "DELETE"):
                c.execute("SELECT has_table_privilege('app_customer', %s, %s)", [t, priv])
                allowed = c.fetchone()[0]
                if t == "audit_event" and priv == "INSERT":
                    assert allowed  # customer activity entries only (D9), policy-checked
                else:
                    assert not allowed, f"app_customer has {priv} on {t}"


def test_customer_role_select_on_base_table_errors(world, as_role):
    with as_role("app_customer", world["A"].customer.id, vendor_tenant_id=world["A"].vendor.id) as c:
        with pytest.raises(ProgrammingError), transaction.atomic():
            c.execute("SELECT * FROM art14_event")


@pytest.mark.parametrize("role", ["app_vendor"])
def test_no_context_gives_zero_rows_everywhere(world, as_role, role):
    for t in tenant_tables():
        with as_role(role) as c:
            c.execute(f'SELECT count(*) FROM "{t}"')
            assert c.fetchone()[0] == 0, t


def test_customer_views_return_zero_rows_without_context(world, as_role):
    for v in ("cust_deployment", "cust_requirement_status", "cust_evidence", "cust_ai_risk", "cust_incident",
              "cust_system_setting"):
        with as_role("app_customer") as c:
            c.execute(f"SELECT count(*) FROM {v}")
            assert c.fetchone()[0] == 0, v


def test_vendor_sees_only_own_rows_in_every_table(world, as_role):
    a, b = world["A"], world["B"]
    for t in tenant_tables():
        with as_role("app_vendor", a.vendor.id, responder=True) as c:
            c.execute(f'SELECT count(*), count(*) FILTER (WHERE vendor_tenant_id <> %s) FROM "{t}"', [str(a.vendor.id)])
            total, foreign = c.fetchone()
        assert foreign == 0, t
    with as_role("app_vendor", a.vendor.id, responder=True) as c:
        c.execute("SELECT count(*) FROM art14_event WHERE id = %s", [str(b.event.id)])
        assert c.fetchone()[0] == 0


def test_vendor_cannot_write_into_another_tenant(world, as_role):
    a, b = world["A"], world["B"]
    with as_role("app_vendor", a.vendor.id) as c:
        c.execute("UPDATE art14_event SET awaiting_responder = false WHERE id = %s", [str(b.drill.id)])
        assert c.rowcount == 0
    with as_role("app_vendor", a.vendor.id) as c:
        with pytest.raises(ProgrammingError), transaction.atomic():  # WITH CHECK violation
            c.execute("""INSERT INTO ai_risk_requirement_link (id, vendor_tenant_id, ai_risk_id, requirement_id)
                         VALUES (gen_random_uuid(), %s, %s, 'CRA-AI-PI-1')""", [str(b.vendor.id), str(b.risk.id)])


def test_incident_details_need_responder_flag(world, as_role):
    a = world["A"]
    with as_role("app_vendor", a.vendor.id, responder=False) as c:
        c.execute("SELECT count(*) FROM art14_event_detail")
        assert c.fetchone()[0] == 0
        c.execute("SELECT count(*) FROM art14_event")
        assert c.fetchone()[0] == 2  # deadline states stay visible to every vendor admin (OQ2)
    with as_role("app_vendor", a.vendor.id, responder=True) as c:
        c.execute("SELECT count(*) FROM art14_event_detail")
        assert c.fetchone()[0] == 1


def test_auth_role_reads_identity_tables_only(world, as_role):
    with as_role("app_auth") as c:
        c.execute("SELECT count(*) FROM user_account")
        assert c.fetchone()[0] >= 6
    with as_role("app_auth") as c:
        with pytest.raises(ProgrammingError), transaction.atomic():
            c.execute("SELECT * FROM art14_event")


def test_customer_views_scope_to_own_deployments(world, as_role):
    a = world["A"]
    with as_role("app_customer", a.customer.id, vendor_tenant_id=a.vendor.id) as c:
        c.execute("SELECT deployment_id FROM cust_deployment")
        assert [str(r[0]) for r in c.fetchall()] == [str(a.deployment.id)]
        c.execute("SELECT count(*), count(DISTINCT deployment_id) FROM cust_requirement_status")
        n, deps = c.fetchone()
        assert n == 27 and deps == 1
        c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='cust_incident'")
        cols = {r[0] for r in c.fetchall()}
    assert not cols & {"awareness_at", "early_warning_filed_at", "notification_filed_at", "final_report_filed_at",
                       "is_drill", "title", "description"}


def test_customer_views_hide_evidence_urls_and_owner_names(world, as_role):
    with connection.cursor() as c:
        for view in ("cust_evidence", "cust_ai_risk", "cust_requirement_status"):
            c.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", [view])
            cols = {r[0] for r in c.fetchall()}
            assert not cols & {"url", "owner_id", "added_by_id", "updated_by_id"}, view
