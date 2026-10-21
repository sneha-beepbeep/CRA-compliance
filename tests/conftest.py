"""Shared fixtures.

Tests under tests/integration, tests/isolation and tests/authz_matrix need a real
PostgreSQL 16 (row-level security, roles, triggers). They are marked `postgres`
automatically and skip cleanly when DATABASE_URL is not set:

    DATABASE_URL=postgres://user:pass@127.0.0.1:5432/tracker pytest

Locally, `scripts/localpg.sh start` prints a suitable URL.
"""
import os
from pathlib import Path

import pytest

HAS_PG = bool(os.environ.get("DATABASE_URL"))
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
