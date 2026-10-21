"""Shared fixtures.

Tests under tests/integration, tests/isolation and tests/authz_matrix need a real
PostgreSQL 16 (row-level security, roles, triggers). They are marked `postgres`
automatically and skip cleanly when DATABASE_URL is not set:

    DATABASE_URL=postgres://user:pass@127.0.0.1:5432/tracker pytest

Locally, `scripts/localpg.sh start` prints a suitable URL.

Production database roles (QA-01): set TEST_LOGIN_ROLE=<name> to run every
test-client request as a non-superuser login role set up exactly as
db/sql/db_roles.sql specifies (app_auth WITH INHERIT TRUE; app_vendor and
app_customer WITH INHERIT FALSE, SET TRUE). Fixtures and ORM assertions still
run as the database owner; only the request path changes. CI runs the suite
both ways.
"""
import os
from pathlib import Path

import pytest

HAS_PG = bool(os.environ.get("DATABASE_URL"))
LOGIN_ROLE = os.environ.get("TEST_LOGIN_ROLE", "")
DEFAULT_LOGIN_ROLE = "tracker_test_app"
PG_DIRS = {"integration", "isolation", "authz_matrix"}
SKIP_PG = pytest.mark.skip(reason="postgres: DATABASE_URL not set (needs PostgreSQL 16 for RLS, roles and triggers)")


def pytest_collection_modifyitems(config, items):
    for item in items:
        parts = set(Path(str(item.fspath)).parts)
        if parts & PG_DIRS:
            item.add_marker(pytest.mark.postgres)
        if item.get_closest_marker("postgres") and not HAS_PG:
            item.add_marker(SKIP_PG)


@pytest.fixture
def catalog(db):
    from apps.catalog.loader import load
    return load()


@pytest.fixture
def world(catalog):
    """Two vendors (A, B), each with a customer, product, version, deployment,
    statuses, an AI risk, a real event and a drill."""
    from apps.tenancy.devdata import seed_vendor
    return {"A": seed_vendor("alpha", "Alpha Scoring GmbH"), "B": seed_vendor("beta", "Beta Lending GmbH")}


@pytest.fixture
def as_role(db):
    """Run raw SQL under an application role with a tenant context, inside the test transaction."""
    from django.db import connection

    class Ctx:
        def __enter__(self):
            return connection.cursor()

        def __exit__(self, *exc):
            with connection.cursor() as c:
                c.execute("RESET ROLE")
                c.execute("SELECT set_config('app.tenant_id','',true), set_config('app.is_responder','',true),"
                          " set_config('app.vendor_tenant_id','',true)")

    def enter(role, tenant_id=None, responder=False, vendor_tenant_id=None):
        with connection.cursor() as c:
            c.execute("SELECT set_config('app.tenant_id', %s, true), set_config('app.is_responder', %s, true),"
                      " set_config('app.vendor_tenant_id', %s, true)",
                      [str(tenant_id or ""), "on" if responder else "", str(vendor_tenant_id or "")])
            c.execute(f"SET LOCAL ROLE {role}")
        return Ctx()

    return enter


def login(client, user):
    client.force_login(user)
    return client


@pytest.fixture(scope="session")
def login_role(django_db_setup, django_db_blocker):
    """Create (idempotently) a non-superuser login role wired as in db_roles.sql."""
    from django.db import connection
    name = LOGIN_ROLE or DEFAULT_LOGIN_ROLE
    with django_db_blocker.unblock():
        # Separate autocommit connection: roles are cluster-wide and must outlive
        # the per-test transaction that is rolled back.
        raw = connection.get_new_connection(connection.get_connection_params())
        raw.autocommit = True
        try:
            with raw.cursor() as c:
                c.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [name])
                if not c.fetchone():
                    c.execute(f'CREATE ROLE "{name}" LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE')
                c.execute(f'GRANT app_auth TO "{name}" WITH INHERIT TRUE')
                c.execute(f'GRANT app_vendor, app_customer TO "{name}" WITH INHERIT FALSE, SET TRUE')
        finally:
            raw.close()
    return name


class _AsRole:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        from django.db import connection
        with connection.cursor() as c:
            c.execute(f'SET SESSION AUTHORIZATION "{self.name}"')

    def __exit__(self, *exc):
        from django.db import connection
        with connection.cursor() as c:
            c.execute("RESET SESSION AUTHORIZATION")


@pytest.fixture
def as_login_role(login_role):
    """Context manager: run code as the non-superuser login role."""
    return lambda: _AsRole(login_role)


@pytest.fixture(autouse=True)
def _requests_as_login_role(request, monkeypatch):
    if not (LOGIN_ROLE and HAS_PG and request.node.get_closest_marker("postgres")):
        yield
        return
    name = request.getfixturevalue("login_role")
    from django.test.client import Client
    original = Client.request

    def request_as_role(self, **kw):
        with _AsRole(name):
            return original(self, **kw)

    monkeypatch.setattr(Client, "request", request_as_role)
    yield


# Browser fixtures (session-scoped, registered once for tests/e2e and tests/a11y).
from tests.browser_support import browser, live_app  # noqa: E402,F401
