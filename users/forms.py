from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm


class QMPasswordResetForm(PasswordResetForm):
    """Only active QM accounts can receive password reset links."""

    def get_users(self, email):
        UserModel = get_user_model()
        email_field_name = UserModel.get_email_field_name()
        active_users = UserModel._default_manager.filter(
            **{
                f"{email_field_name}__iexact": email,
                "is_active": True,
                "status": UserModel.Status.ACTIVE,
            }
        )
        return (
            user
            for user in active_users
            if user.has_usable_password()
        )
