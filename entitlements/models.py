import uuid

from django.db import models
from django.utils import timezone

from organizations.models import Organization


class ProductEntitlement(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="entitlements",
    )
    product_id = models.SlugField(max_length=64)
    plan = models.CharField(max_length=64, blank=True, default="")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "product_id"],
                name="uq_entitlement_org_product",
            ),
        ]

    def is_active_at(self, at=None):
        at = at or timezone.now()
        if self.status != self.Status.ACTIVE:
            return False
        if self.valid_from and self.valid_from > at:
            return False
        if self.valid_until and self.valid_until <= at:
            return False
        return True

    def __str__(self):
        return f"{self.organization.slug}:{self.product_id}:{self.status}"


class OAuthClientPolicy(models.Model):
    """Least-privilege policy for one registered OAuth/OIDC application."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application_client_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=200, blank=True, default="")
    is_active = models.BooleanField(default=True)
    can_provision_accounts = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def allows_product(self, product_id):
        return (
            self.is_active
            and self.product_grants.filter(product_id=product_id).exists()
        )

    def __str__(self):
        return self.name or self.application_client_id


class OAuthClientProductGrant(models.Model):
    """Product allowlist entry for an OAuth/OIDC client."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_policy = models.ForeignKey(
        OAuthClientPolicy,
        on_delete=models.CASCADE,
        related_name="product_grants",
    )
    product_id = models.SlugField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["client_policy", "product_id"],
                name="uq_oauth_client_policy_product",
            ),
        ]

    def __str__(self):
        return f"{self.client_policy}:{self.product_id}"
