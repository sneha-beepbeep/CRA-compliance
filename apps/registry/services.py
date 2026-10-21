"""Product registry and setup checklist (F-1)."""
from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from apps.audit.log import record
from apps.catalog.models import CategoryRequirementSet, Requirement
from apps.core import clock
from apps.requirements.models import RequirementStatus
from apps.tenancy.models import ActivitySharingSetting, Tenant

from .models import Deployment, Product, ProductVersion

HOSTED_ONLY_WARNING = ("The CRA may not apply to a product delivered only as a hosted service. "
                       "Check scope with legal counsel.")


class RegistryError(ValueError):
    pass


def requirements_for_category(category_id):
    set_ids = CategoryRequirementSet.objects.filter(category_id=category_id).values_list("requirement_set_id", flat=True)
    return Requirement.objects.filter(requirement_set_id__in=list(set_ids))


@transaction.atomic
def create_product(request, *, name, intended_purpose, category, delivery_model=""):
    if not category.supported:
        raise RegistryError(f"{category.citation} – not yet supported")
    p = Product.objects.create(vendor_tenant_id=request.tenant_ctx.vendor_tenant_id, name=name.strip(),
                               intended_purpose=intended_purpose.strip(), category=category,
                               delivery_model=delivery_model)
    record(request, area="registry", action="added_product", target=p, target_label=p.name,
           new={"name": p.name, "category": category.code, "delivery_model": delivery_model})
    return p


@transaction.atomic
def create_version(request, *, product, label, release_date=None):
    v = ProductVersion.objects.create(vendor_tenant_id=product.vendor_tenant_id, product=product,
                                      label=label.strip(), release_date=release_date)
    reqs = requirements_for_category(product.category_id).filter(context_only=False)
    RequirementStatus.objects.bulk_create([
        RequirementStatus(vendor_tenant_id=product.vendor_tenant_id, version=v, requirement=r) for r in reqs])
    record(request, area="registry", action="added_version", target=v, target_label=str(v),
           new={"label": v.label, "release_date": release_date, "requirements_attached": reqs.count()})
    return v


@transaction.atomic
def create_deployment(request, *, product, version, label, customer_name):
    ctx = request.tenant_ctx
    customer_name = customer_name.strip()
    customer = Tenant.objects.filter(kind=Tenant.Kind.CUSTOMER, display_name__iexact=customer_name).first()
    if customer is None:
        customer = Tenant(kind=Tenant.Kind.CUSTOMER, vendor_tenant_id=ctx.vendor_tenant_id,
                          legal_name=customer_name, display_name=customer_name)
        customer.save()
        ActivitySharingSetting.objects.create(vendor_tenant_id=ctx.vendor_tenant_id, customer_tenant=customer)
        record(request, area="registry", action="added_customer", target=customer, target_label=customer_name)
    d = Deployment.objects.create(vendor_tenant_id=ctx.vendor_tenant_id, customer_tenant=customer, product=product,
                                  version=version, label=label.strip(), version_changed_at=clock.now())
    record(request, area="registry", action="added_deployment", target=d, target_label=d.label,
           new={"customer": customer.display_name, "version": version.label if version else None})
    return d


@transaction.atomic
def change_deployment_version(request, deployment, version):
    old = deployment.version.label if deployment.version else None
    deployment.version = version
    deployment.version_changed_at = clock.now()
    deployment.save(update_fields=["version", "version_changed_at"])
    record(request, area="registry", action="changed_deployment_version", target=deployment,
           target_label=deployment.label, old={"version": old}, new={"version": version.label})


@dataclass(frozen=True)
class Step:
    label: str
    done: bool
    url: str
    optional: bool = False


@dataclass(frozen=True)
class Checklist:
    """Setup checklist (F-1). Only required steps count toward completion;
    optional steps are listed separately and never change the count (deviation 13)."""

    required: list
    optional: list

    @property
    def done_count(self) -> int:
        return sum(1 for s in self.required if s.done)

    @property
    def total(self) -> int:
        return len(self.required)

    @property
    def complete(self) -> bool:
        return self.done_count == self.total


def setup_checklist(request) -> Checklist:
    from django.conf import settings

    from apps.art14.services import responders
    from apps.tenancy.models import CustomerInvitation

    ctx = request.tenant_ctx
    products = Product.objects.all()
    required = [
        Step("Add a product", products.exists(), "/setup/"),
        Step("Add a version", ProductVersion.objects.exists(), "/setup/"),
        Step("Select the Annex III category", products.filter(category__supported=True).exists(), "/setup/"),
        Step("Assign at least one incident responder", bool(responders(ctx.vendor_tenant_id)), "/setup/users/"),
        Step("Add a deployment", Deployment.objects.exists(), "/setup/"),
        Step("Confirm your time zone", bool(request.user.time_zone_confirmed), "/profile/"),
    ]
    optional = []
    # Hidden until customer invitations exist (phase 1b); CPO decision 2026-10-21.
    if settings.CUSTOMER_INVITATIONS_ENABLED:
        optional.append(Step("Invite a customer admin",
                             CustomerInvitation.objects.filter(revoked_at__isnull=True).exists(), "/setup/",
                             optional=True))
    return Checklist(required, optional)
