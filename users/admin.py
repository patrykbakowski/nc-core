from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import ExternalIdentity, User


class QMUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email",)


class QMUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"


@admin.register(User)
class QMUserAdmin(UserAdmin):
    add_form = QMUserCreationForm
    form = QMUserChangeForm
    model = User
    ordering = ("email",)
    list_display = ("email", "status", "is_active", "is_staff", "last_login")
    list_filter = ("status", "is_active", "is_staff", "is_superuser")
    search_fields = ("email", "first_name", "last_name")
    readonly_fields = ("last_login", "date_joined")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("first_name", "last_name")}),
        (
            "Account status",
            {"fields": ("status", "is_active", "is_staff", "is_superuser")},
        ),
        (
            "Permissions",
            {"fields": ("groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "status",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
    filter_horizontal = ("groups", "user_permissions")


@admin.register(ExternalIdentity)
class ExternalIdentityAdmin(admin.ModelAdmin):
    list_display = ("provider", "external_subject", "user", "created_at")
    list_filter = ("provider",)
    search_fields = ("external_subject", "user__email")
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
