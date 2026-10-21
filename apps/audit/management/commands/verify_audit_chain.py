"""Verify every vendor's audit hash chain and print the chain heads (QA-09).

A hash chain alone can't detect deletion of its newest rows. Anchor the heads
outside the database: run this on a schedule, ship the JSON output to the log
store (or object storage with retention), and pass the previous output back
with --anchors. A recorded head whose seq/hash is no longer in the chain means
entries were removed.

Exit status 1 on any break, so a scheduler can raise it.
"""
import json
import sys

from django.core.management.base import BaseCommand
from django.db import connection

from apps.audit.models import AuditEvent
from apps.tenancy.models import Tenant


class Command(BaseCommand):
    help = "Verify audit hash chains; print heads as JSON; compare with --anchors from a previous run."

    def add_arguments(self, parser):
        parser.add_argument("--anchors", help="JSON file from a previous run")

    def handle(self, *args, anchors=None, **opts):
        previous = {}
        if anchors:
            with open(anchors, encoding="utf-8") as fh:
                previous = {h["vendor_tenant_id"]: h for h in json.load(fh)["heads"]}
        heads, problems = [], []
        for vid in Tenant.objects.filter(kind="vendor").values_list("id", flat=True).order_by("id"):
            vid = str(vid)
            with connection.cursor() as c:
                c.execute("SELECT audit_verify_chain(%s)", [vid])
                broken = c.fetchone()[0]
            if broken is not None:
                problems.append(f"{vid}: chain broken at seq {broken}")
            head = AuditEvent.objects.filter(vendor_tenant_id=vid).order_by("-seq").values("seq", "hash").first()
            heads.append({"vendor_tenant_id": vid, "seq": head["seq"] if head else None,
                          "hash": head["hash"] if head else None})
            old = previous.get(vid)
            if old and old["seq"] is not None:
                still = AuditEvent.objects.filter(vendor_tenant_id=vid, seq=old["seq"], hash=old["hash"]).exists()
                if not still:
                    problems.append(f"{vid}: anchored head seq {old['seq']} is missing or changed (entries removed)")
        self.stdout.write(json.dumps({"heads": heads, "problems": problems}, indent=2))
        if problems:
            sys.exit(1)
