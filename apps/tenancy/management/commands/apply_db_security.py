from django.core.management.base import BaseCommand

from apps.tenancy.dbsecurity import ORDER, apply_all


class Command(BaseCommand):
    help = "Re-apply database roles, RLS policies, customer views, cra_deadline_check, audit and drill guards."

    def handle(self, *args, **opts):
        apply_all()
        self.stdout.write("Applied: " + ", ".join(ORDER))
