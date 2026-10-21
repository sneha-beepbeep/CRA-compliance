"""Tenancy: tenants, user accounts, role grants, invitations, settings."""
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models import Q

from apps.core.models import TenantScoped, UUIDModel


class Tenant(UUIDModel):
    class Kind(models.TextChoices):
        VENDOR = "vendor"
        CUSTOMER = "customer"

    kind = models.CharField(max_length=16, choices=Kind.choices)
    # For a vendor tenant this is the tenant itself; for a customer tenant it is
    # the parent vendor. Lets every RLS policy key on one column.
    vendor_tenant = models.ForeignKey("self", on_delete=models.PROTECT, null=True, related_name="+",
                                      db_column="vendor_tenant_id")
    legal_name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tenant"
        constraints = [models.CheckConstraint(condition=Q(kind__in=["vendor", "customer"]), name="tenant_kind")]

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        if self.kind == self.Kind.VENDOR:
            self.vendor_tenant_id = self.id
        super().save(*args, **kwargs)

    @property
    def is_vendor(self):
        return self.kind == self.Kind.VENDOR


class UserAccountManager(BaseUserManager):
    def create_user(self, email, tenant, display_name, **extra):
        user = self.model(email=self.normalize_email(email), tenant=tenant,
                          vendor_tenant_id=tenant.vendor_tenant_id or tenant.id,
                          display_name=display_name, **extra)
        user.set_unusable_password()  # sign-in is through the identity service only
        user.save(using=self._db)
        return user


class UserAccount(AbstractBaseUser, TenantScoped):
    """A user belongs to exactly one tenant (design 11.3)."""

    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="users")
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=200)
    oidc_subject = models.CharField(max_length=255, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    # Vendor access managers grant/remove the responder role and invite customers.
    is_access_manager = models.BooleanField(default=False)
    # Until the user confirms a zone (one-time banner, option D), times show in UTC.
    time_zone = models.CharField(max_length=64, default="UTC")
    time_zone_confirmed = models.BooleanField(default=False)
    time_zone_confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]
    objects = UserAccountManager()

    class Meta:
        db_table = "user_account"

    def __str__(self):
        return self.display_name

    @property
    def short_name(self):
        parts = self.display_name.split()
        return f"{parts[0][0]}. {' '.join(parts[1:])}" if len(parts) > 1 else self.display_name


class RoleGrant(TenantScoped):
    """Role grants with history. Never deleted; revoked by setting revoked_at."""

    class Role(models.TextChoices):
        INCIDENT_RESPONDER = "incident_responder"

    user = models.ForeignKey(UserAccount, on_delete=models.PROTECT, related_name="role_grants")
    role = models.CharField(max_length=32, choices=Role.choices)
    granted_by = models.ForeignKey(UserAccount, on_delete=models.PROTECT, related_name="+", null=True)
    granted_at = models.DateTimeField()
    revoked_by = models.ForeignKey(UserAccount, on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "role_grant"
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], condition=Q(revoked_at__isnull=True),
                                    name="role_grant_one_active"),
        ]


class CustomerInvitation(TenantScoped):
    customer_tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="+")
    email = models.EmailField()
    invited_by = models.ForeignKey(UserAccount, on_delete=models.PROTECT, related_name="+")
    invited_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "customer_invitation"


class ActivitySharingSetting(TenantScoped):
    """D9: organisation-wide; 'organisation' applies until someone chooses."""

    class Mode(models.TextChoices):
        NAMED = "named"
        ORGANISATION = "organisation"

    customer_tenant = models.OneToOneField(Tenant, on_delete=models.PROTECT, related_name="activity_sharing")
    mode = models.CharField(max_length=16, choices=Mode.choices, default=Mode.ORGANISATION)
    chosen = models.BooleanField(default=False)
    changed_by = models.ForeignKey(UserAccount, on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    changed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "activity_sharing_setting"


class SystemSetting(models.Model):
    """Global configuration (disclaimer template, month_rule, retention).

    Changed by operators through `manage.py set_system_setting` (audited in every vendor
    tenant's trail; see apps/tenancy/settings_admin.py); no release needed.
    """

    key = models.CharField(max_length=64, primary_key=True)
    value = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "system_setting"

    DEFAULTS = {
        "month_rule": "calendar_clamp_utc",
        "disclaimer_template": ("Status reflects information entered by {vendor_legal_name}. "
                                "It is not a determination of compliance."),
        "month_rule_note": "Calculated as one calendar month. Pending legal confirmation.",
    }

    @classmethod
    def get(cls, key):
        row = cls.objects.filter(key=key).first()
        return row.value if row else cls.DEFAULTS.get(key)
