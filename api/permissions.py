from rest_framework.permissions import BasePermission


def _token_scopes(request):
    token = getattr(request, "auth", None)
    if token is None:
        return set()
    return set((getattr(token, "scope", "") or "").split())


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


class HasQMAccessScopeOrSession(BasePermission):
    """Session users may call the endpoint; OAuth tokens need the qm.access scope."""

    def has_permission(self, request, view):
        token = getattr(request, "auth", None)
        if token is None:
            return True
        return "qm.access" in _token_scopes(request)


class HasQMProvisionScope(BasePermission):
    """Service OAuth token must explicitly carry qm.provision."""

    def has_permission(self, request, view):
        token = getattr(request, "auth", None)
        return bool(
            token
            and getattr(token, "application_id", None)
            and "qm.provision" in _token_scopes(request)
        )
