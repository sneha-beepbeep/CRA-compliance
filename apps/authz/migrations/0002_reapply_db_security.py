"""Re-applies db/sql/*.sql after QA fixes (QA-01 app_auth last_login policy,
QA-02 closed-event guard, QA-09 audit_verify_chain scoping)."""
from django.db import migrations

from apps.tenancy.dbsecurity import apply_migration


class Migration(migrations.Migration):
    dependencies = [("authz", "0001_database_security")]
    operations = [migrations.RunPython(apply_migration, migrations.RunPython.noop)]
