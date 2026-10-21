"""Product registry (D3: status per product version, with carry-forward)."""
from django.db import models

from apps.core.models import TenantScoped


class Product(TenantScoped):
    class DeliveryModel(models.TextChoices):
        INSTALLED = "installed", "Installed software"
        SDK = "sdk", "SDK or library"
        HOSTED_WITH_CLIENT = "hosted_with_client", "Hosted API with vendor software on the customer side"
        HOSTED_ONLY = "hosted_only", "Browser-only or hosted API only"

    name = models.CharField(max_length=200)
    intended_purpose = models.TextField()
    category = models.ForeignKey("catalog.AnnexIIICategory", on_delete=models.PROTECT)
    delivery_model = models.CharField(max_length=32, choices=DeliveryModel.choices, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductVersion(TenantScoped):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="versions")
    label = models.CharField(max_length=64)
    release_date = models.DateField(null=True, blank=True)
    carried_forward_from = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True,
                                             related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_version"
        ordering = ["product__name", "-created_at"]
        constraints = [models.UniqueConstraint(fields=["product", "label"], name="product_version_label")]

    def __str__(self):
        return f"{self.product.name} {self.label}"


class Deployment(TenantScoped):
    customer_tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.PROTECT, related_name="deployments")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="deployments")
    version = models.ForeignKey(ProductVersion, on_delete=models.PROTECT, null=True, blank=True,
                                related_name="deployments")
    label = models.CharField(max_length=200)
    version_changed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "deployment"
        ordering = ["label"]

    def __str__(self):
        return self.label
