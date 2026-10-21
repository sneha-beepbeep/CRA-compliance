"""Applies db/sql/*.sql: roles, RLS, cust_* views, cra_deadline_check, audit and drill guards.

The SQL files are idempotent. Any later migration that adds a tenant table must
add a migration calling apps.tenancy.dbsecurity.apply_migration again; the
isolation suite fails if a table with vendor_tenant_id lacks RLS.
"""
from django.db import migrations

from apps.tenancy.dbsecurity import apply_migration


class Migration(migrations.Migration):
    dependencies = [
        ("sessions", "0001_initial"),
        ("airisks", "0001_initial"),
        ("art14", "0001_initial"),
        ("audit", "0001_initial"),
        ("catalog", "0001_initial"),
        ("exports", "0001_initial"),
        ("imports", "0001_initial"),
        ("registry", "0001_initial"),
        ("requirements", "0001_initial"),
        ("tenancy", "0001_initial"),
    ]

    operations = [migrations.RunPython(apply_migration, migrations.RunPython.noop)]
