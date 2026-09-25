from rest_framework.permissions import BasePermission


class IsActiveQMUser(BasePermission):
    """Require an authenticated Django user whose QM account is active."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and getattr(user, "status", None) == "active"
        )
