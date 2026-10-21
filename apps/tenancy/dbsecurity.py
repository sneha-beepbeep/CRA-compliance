"""Applies db/sql/*.sql in order. Used by the security migration and by
`manage.py apply_db_security` (re-run after any migration that adds tables)."""
from pathlib import Path

from django.conf import settings
from django.db import connection

SQL_DIR = Path(settings.BASE_DIR) / "db" / "sql"
ORDER = ["db_roles.sql", "rls_policies.sql", "customer_views.sql", "cra_deadline_check.sql",
         "audit_append_only.sql", "drill_guards.sql"]


def apply_all(conn=None):
    conn = conn or connection
    with conn.cursor() as cur:
        for name in ORDER:
            cur.execute((SQL_DIR / name).read_text(encoding="utf-8"))


def apply_migration(apps, schema_editor):
    apply_all(schema_editor.connection)
