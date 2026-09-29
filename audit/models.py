import uuid

from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    class ActorType(models.TextChoices):
        USER = "user", "User"
        OAUTH_CLIENT = "oauth_client", "OAuth client"
        SYSTEM = "system", "System"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    occurred_at = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=96)
    actor_type = models.CharField(max_length=24, choices=ActorType.choices)
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="identity_audit_events",
    )
    oauth_client_id = models.CharField(max_length=255, blank=True, default="")
    target_type = models.CharField(max_length=96, blank=True, default="")
    target_id = models.CharField(max_length=255, blank=True, default="")
    organization_id = models.UUIDField(null=True, blank=True)
    product_id = models.SlugField(max_length=64, blank=True, default="")
    metadata_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-occurred_at",)
        indexes = [
            models.Index(fields=["event_type", "occurred_at"], name="audit_event_type_at_idx"),
            models.Index(fields=["oauth_client_id", "occurred_at"], name="audit_client_at_idx"),
            models.Index(fields=["organization_id", "occurred_at"], name="audit_org_at_idx"),
        ]

    def __str__(self):
        return f"{self.occurred_at.isoformat()}:{self.event_type}"
