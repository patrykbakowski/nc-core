from django.contrib.auth.backends import ModelBackend


class QMModelBackend(ModelBackend):
    """Django auth backend that treats QM account status as an auth boundary."""

    def user_can_authenticate(self, user):
        return (
            super().user_can_authenticate(user)
            and getattr(user, "status", None) == "active"
        )
