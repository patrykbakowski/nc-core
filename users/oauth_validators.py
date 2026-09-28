from oauth2_provider.oauth2_validators import OAuth2Validator


class QMOAuth2Validator(OAuth2Validator):
    """Expose only stable identity claims. Authorization stays queryable at runtime."""

    def get_additional_claims(self, request):
        user = request.user
        return {
            "email": user.email,
            "given_name": user.first_name,
            "family_name": user.last_name,
            "name": user.get_full_name().strip(),
        }
