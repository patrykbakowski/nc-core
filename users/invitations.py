from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


class QMInvitationTokenGenerator(PasswordResetTokenGenerator):
    key_salt = "qm_identity.invitation"

    def _make_hash_value(self, user, timestamp):
        return "|".join(
            [
                str(user.pk),
                user.password,
                str(timestamp),
                str(user.is_active),
                user.status,
                user.email,
                "qm-invite-v1",
            ]
        )


invitation_tokens = QMInvitationTokenGenerator()


def invitation_path(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = invitation_tokens.make_token(user)
    return f"/accounts/invite/{uid}/{token}/"
