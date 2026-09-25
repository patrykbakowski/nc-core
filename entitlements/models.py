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
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="entitlements")
    product_id = models.SlugField(max_length=64)
    plan = models.CharField(max_length=64, blank=True, default="")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["organization", "product_id"], name="uq_entitlement_org_product"),
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
