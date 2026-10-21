"""Development and test data. Runs with the login role (no tenant context).

Never used in production; `manage.py seed_dev` refuses to run unless DEBUG.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from apps.art14.models import Art14Event, Art14EventDetail
from apps.catalog.models import AnnexIIICategory
from apps.registry.models import Deployment, Product, ProductVersion
from apps.registry.services import requirements_for_category
from apps.requirements.models import RequirementStatus
from apps.airisks.models import AIRisk

from .models import ActivitySharingSetting, RoleGrant, Tenant, UserAccount

UTC = timezone.utc


@dataclass
class VendorWorld:
    vendor: Tenant
    manager: UserAccount      # vendor admin + access manager + incident responder
    admin: UserAccount        # vendor admin only
    customer: Tenant
    customer_user: UserAccount
    product: Product
    version: ProductVersion
    deployment: Deployment
    status: RequirementStatus
    risk: AIRisk
    event: Art14Event         # real event (created directly; C6 doesn't apply to fixtures)
    drill: Art14Event


def seed_vendor(key: str, legal_name: str, now: datetime | None = None) -> VendorWorld:
    now = (now or datetime.now(UTC)).replace(second=0, microsecond=0)
    vendor = Tenant(kind=Tenant.Kind.VENDOR, legal_name=legal_name, display_name=legal_name.split(" GmbH")[0])
    vendor.save()
    mk = UserAccount.objects.create_user
    manager = mk(f"responder@{key}.example", vendor, f"Tomasz {key.title()}", is_access_manager=True,
                 time_zone="Europe/Warsaw", time_zone_confirmed=True)
    admin = mk(f"admin@{key}.example", vendor, f"Lena {key.title()}", time_zone="Europe/Berlin")
    RoleGrant.objects.create(vendor_tenant=vendor, user=manager, role=RoleGrant.Role.INCIDENT_RESPONDER,
                             granted_at=now)
    customer = Tenant(kind=Tenant.Kind.CUSTOMER, vendor_tenant=vendor, legal_name=f"Customer of {key}",
                      display_name=f"Customer {key.title()}")
    customer.save()
    ActivitySharingSetting.objects.create(vendor_tenant=vendor, customer_tenant=customer)
    customer_user = mk(f"jan@customer-{key}.example", customer, f"Jan {key.title()}")
    cat = AnnexIIICategory.objects.get(code="5(b)")
    product = Product.objects.create(vendor_tenant=vendor, name=f"ScoreEngine {key}", intended_purpose="Credit scoring",
                                     category=cat, delivery_model="installed")
    version = ProductVersion.objects.create(vendor_tenant=vendor, product=product, label="4.2")
    reqs = list(requirements_for_category(cat.code).filter(context_only=False))
    RequirementStatus.objects.bulk_create(
        [RequirementStatus(vendor_tenant=vendor, version=version, requirement=r) for r in reqs])
    deployment = Deployment.objects.create(vendor_tenant=vendor, customer_tenant=customer, product=product,
                                           version=version, label=f"Customer {key.title()} – prod")
    risk = AIRisk.objects.create(vendor_tenant=vendor, version=version, name="Training-data poisoning",
                                 attack_class="data_poisoning")
    event = Art14Event.objects.create(
        vendor_tenant=vendor, ref_number=1, event_type="vulnerability", awareness_at=now - timedelta(hours=2),
        product=product, product_version=version, assigned_responder=manager, started_by=manager,
        started_via="log_event", started_at=now, is_drill=False)
    Art14EventDetail.objects.create(vendor_tenant=vendor, event=event, title=f"Secret title {key}",
                                    description="Exploit detail that only responders may read.")
    drill = Art14Event.objects.create(
        vendor_tenant=vendor, ref_number=2, event_type="severe_incident", awareness_at=now - timedelta(hours=1),
        product=product, assigned_responder=manager, started_by=admin, started_via="start_clock", started_at=now,
        awaiting_responder=True, is_drill=True)
    return VendorWorld(vendor, manager, admin, customer, customer_user, product, version, deployment,
                       RequirementStatus.objects.filter(version=version).first(), risk, event, drill)
