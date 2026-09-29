from django.contrib import admin

from .models import (
    OAuthClientPolicy,
    OAuthClientProductGrant,
    ProductEntitlement,
)


@admin.register(ProductEntitlement)
class ProductEntitlementAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "product_id",
        "plan",
        "status",
        "valid_from",
        "valid_until",
    )
    list_filter = ("product_id", "status", "plan")
    search_fields = ("organization__name", "organization__slug", "product_id")
    autocomplete_fields = ("organization",)
    readonly_fields = ("created_at",)


class OAuthClientProductGrantInline(admin.TabularInline):
    model = OAuthClientProductGrant
    extra = 0
    fields = ("product_id", "created_at")
    readonly_fields = ("created_at",)


@admin.register(OAuthClientPolicy)
class OAuthClientPolicyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "application_client_id",
        "is_active",
        "can_provision_accounts",
        "updated_at",
    )
    list_filter = ("is_active", "can_provision_accounts")
    search_fields = ("name", "application_client_id")
    readonly_fields = ("created_at", "updated_at")
    inlines = (OAuthClientProductGrantInline,)


@admin.register(OAuthClientProductGrant)
class OAuthClientProductGrantAdmin(admin.ModelAdmin):
    list_display = ("client_policy", "product_id", "created_at")
    list_filter = ("product_id",)
    search_fields = (
        "client_policy__name",
        "client_policy__application_client_id",
        "product_id",
    )
    autocomplete_fields = ("client_policy",)
    readonly_fields = ("created_at",)
