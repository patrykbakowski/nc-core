from django.contrib.auth import logout


class ActiveQMAccountMiddleware:
    """Drop an existing central session as soon as the QM account is no longer active."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            user
            and user.is_authenticated
            and (
                not user.is_active
                or getattr(user, "status", None) != "active"
            )
        ):
            logout(request)
        return self.get_response(request)
