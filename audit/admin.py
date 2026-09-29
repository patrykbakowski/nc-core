from django.contrib import admin

from .models import AuditEvent
from .service import record_admin_event


class IdentityAuditAdminMixin:
    """Mirror Django-admin mutations into the QM identity/access audit stream."""

    def log_addition(self, request, obj, message):
        super().log_addition(request, obj, message)
        record_admin_event(
            request,
            "admin.object.created",
            obj,
            metadata={"changes": str(message)},
        )

    def log_change(self, request, obj, message):
        super().log_change(request, obj, message)
        record_admin_event(
            request,
            "admin.object.changed",
            obj,
            metadata={"changes": str(message)},
        )

    def log_deletion(self, request, obj, object_repr):
        record_admin_event(
            request,
            "admin.object.deleted",
            obj,
            metadata={"object_repr": object_repr},
        )
        super().log_deletion(request, obj, object_repr)


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = (
        "occurred_at",
        "event_type",
        "actor_type",
        "actor_user",
        "oauth_client_id",
        "target_type",
        "target_id",
        "organization_id",
        "product_id",
    )
    list_filter = ("actor_type", "event_type", "product_id")
    search_fields = (
        "oauth_client_id",
        "target_type",
        "target_id",
        "actor_user__email",
    )
    readonly_fields = tuple(field.name for field in AuditEvent._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
