from django.contrib import admin

from audit.admin import IdentityAuditAdminMixin

from .models import Membership, Organization


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    autocomplete_fields = ("user",)
    fields = ("user", "role", "status", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Organization)
class OrganizationAdmin(IdentityAuditAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "slug")
    readonly_fields = ("created_at",)
    inlines = (MembershipInline,)


@admin.register(Membership)
class MembershipAdmin(IdentityAuditAdminMixin, admin.ModelAdmin):
    list_display = ("organization", "user", "role", "status", "created_at")
    list_filter = ("role", "status", "organization")
    search_fields = ("organization__name", "organization__slug", "user__email")
    autocomplete_fields = ("organization", "user")
    readonly_fields = ("created_at",)
