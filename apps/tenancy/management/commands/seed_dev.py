from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from apps.tenancy.devdata import seed_vendor
from apps.tenancy.models import Tenant


class Command(BaseCommand):
    help = "Development only: load the catalog and create two sample vendor tenants."

    def handle(self, *args, **opts):
        if not settings.DEBUG:
            raise CommandError("seed_dev runs only with DEBUG settings.")
        call_command("load_catalog")
        if Tenant.objects.filter(kind="vendor").exists():
            self.stdout.write("Sample tenants already exist.")
            return
        for key, name in (("acme", "Acme Scoring GmbH"), ("other", "Other Lending Tech GmbH")):
            w = seed_vendor(key, name)
            self.stdout.write(f"{name}: responder {w.manager.email}, admin {w.admin.email}, "
                              f"customer {w.customer_user.email}")
