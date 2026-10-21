"""QA-01 regression: sign-in and requests through a NON-superuser login role,
set up as db/sql/db_roles.sql specifies. Runs on every Postgres run (CI too)."""
import pytest
from django.contrib.auth import login
from django.contrib.sessions.middleware import SessionMiddleware
from django.db import connection, transaction
from django.db.utils import DatabaseError, ProgrammingError
from django.test import Client, RequestFactory

from apps.tenancy.models import UserAccount

pytestmark = pytest.mark.django_db


def test_login_role_is_least_privilege(login_role):
    with connection.cursor() as c:
        c.execute("SELECT rolsuper, rolbypassrls, rolcreaterole, rolcreatedb FROM pg_roles WHERE rolname=%s",
                  [login_role])
        assert c.fetchone() == (False, False, False, False)
        c.execute("""SELECT r.rolname, m.inherit_option, m.set_option FROM pg_auth_members m
                     JOIN pg_roles r ON r.oid = m.roleid JOIN pg_roles u ON u.oid = m.member
                     WHERE u.rolname = %s ORDER BY 1""", [login_role])
        assert c.fetchall() == [("app_auth", True, True), ("app_customer", False, True), ("app_vendor", False, True)]


def _login_request(user):
    r = RequestFactory().get("/")
    SessionMiddleware(lambda req: None).process_request(r)
    login(r, user, backend="apps.identity.oidc.TrackerOIDCBackend")  # updates last_login (QA-01)
    r.session.save()
    return r


def test_sign_in_updates_last_login_as_login_role(world, as_login_role):
    user = world["A"].admin
    assert user.last_login is None
    with as_login_role():
        _login_request(user)
    user.refresh_from_db()
    assert user.last_login is not None


def test_regression_guard_without_policy_sign_in_fails(world, as_login_role):
    """Proves this test would have caught QA-01: drop the policy and login breaks."""
    with connection.cursor() as c:
        c.execute("DROP POLICY auth_last_login ON user_account")
    with as_login_role():
        with pytest.raises(DatabaseError, match="did not affect any rows"), transaction.atomic():
            _login_request(world["A"].admin)


def test_auth_role_cannot_change_other_columns_or_inactive_users(world, as_login_role):
    a = world["A"]
    with as_login_role(), connection.cursor() as c:
        with pytest.raises(ProgrammingError, match="permission denied"), transaction.atomic():
            c.execute("UPDATE user_account SET email='x@evil.example' WHERE id=%s", [str(a.admin.pk)])
    UserAccount.objects.filter(pk=a.admin.pk).update(is_active=False)
    with as_login_role(), connection.cursor() as c:
        c.execute("UPDATE user_account SET last_login=now() WHERE id=%s", [str(a.admin.pk)])
        assert c.rowcount == 0
    with as_login_role(), connection.cursor() as c:
        with pytest.raises(ProgrammingError, match="permission denied"), transaction.atomic():
            c.execute("DELETE FROM user_account")


def test_auth_role_sees_no_tenant_data(world, as_login_role):
    with as_login_role(), connection.cursor() as c:
        with pytest.raises(ProgrammingError, match="permission denied"), transaction.atomic():
            c.execute("SELECT count(*) FROM art14_event")


def test_full_request_path_as_login_role(world, as_login_role):
    """Session load, user lookup, responder check, SET LOCAL ROLE, view, session save."""
    a = world["A"]
    c = Client()
    with as_login_role():
        c.force_login(a.manager)  # auth.login -> last_login update as the login role
    with as_login_role():
        r = c.get(f"/events/{a.event.pk}/")
        body = r.content.decode()
        strip = c.get("/clocks/strip")
        other = c.get(f"/events/{world['B'].event.pk}/")
    assert r.status_code == 200 and "Secret title alpha" in body
    assert strip.status_code == 200 and other.status_code == 404


def test_suite_mode_routes_requests_through_login_role(world):
    """With TEST_LOGIN_ROLE set, every test-client request runs as that role (CI runs this mode)."""
    from django.core.signals import request_started

    from tests.conftest import LOGIN_ROLE
    if not LOGIN_ROLE:
        pytest.skip("only meaningful when the suite runs with TEST_LOGIN_ROLE (second CI run)")
    seen = []

    def record(**kw):
        with connection.cursor() as c:
            c.execute("SELECT session_user, current_setting('is_superuser')")
            seen.append(c.fetchone())

    request_started.connect(record)
    try:
        c = Client()
        c.force_login(world["A"].manager)
        assert c.get("/").status_code == 200
    finally:
        request_started.disconnect(record)
    assert seen == [(LOGIN_ROLE, "off")]
