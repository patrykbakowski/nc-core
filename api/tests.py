from datetime import timedelta
import uuid

from django.contrib.auth import authenticate, get_user_model
from django.test import TestCase
from django.utils import timezone
from oauth2_provider.models import get_access_token_model, get_application_model
from rest_framework.test import APIClient

from entitlements.models import ProductEntitlement
from organizations.models import Membership, Organization

User = get_user_model()
Application = get_application_model()
AccessToken = get_access_token_model()


class AccessContextTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@example.com",
            password="correct horse battery staple",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="other password 123",
        )
        self.org = Organization.objects.create(name="Acme", slug="acme")
        self.other_org = Organization.objects.create(name="Other", slug="other")
        self.membership = Membership.objects.create(
            organization=self.org,
            user=self.user,
            role=Membership.Role.ADMIN,
        )
        Membership.objects.create(
            organization=self.other_org,
            user=self.other_user,
            role=Membership.Role.OWNER,
        )
        self.entitlement = ProductEntitlement.objects.create(
            organization=self.org,
            product_id="zgodomat",
            plan="pilot",
        )

    def login(self):
        return self.client.post(
            "/api/v1/auth/login/",
            {"email": self.user.email, "password": "correct horse battery staple"},
            format="json",
        )

    def bearer(self, scope="openid profile email qm.access"):
        application = Application.objects.create(
            user=self.user,
            name="QM test client",
            client_type="confidential",
            authorization_grant_type="authorization-code",
            redirect_uris="https://client.example/callback",
        )
        token = AccessToken.objects.create(
            user=self.user,
            application=application,
            token=f"test-token-{uuid.uuid4()}",
            expires=timezone.now() + timedelta(minutes=10),
            scope=scope,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.token}")
        return token

    def test_email_login_and_me(self):
        self.assertIsInstance(self.user.pk, uuid.UUID)
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": self.user.email.upper(), "password": "correct horse battery staple"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["email"], self.user.email)
        self.assertEqual(len(response.data["memberships"]), 1)
        self.assertEqual(response.data["memberships"][0]["role"], Membership.Role.ADMIN)

    def test_invalid_login_is_rejected(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": self.user.email, "password": "wrong"},
            format="json",
        )
        self.assertIn(response.status_code, (401, 403))

    def test_valid_zgodomat_context(self):
        self.login()
        response = self.client.get(
            "/api/v1/access-context/",
            {"organization_id": str(self.org.pk), "product": "zgodomat"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["membership"]["role"], Membership.Role.ADMIN)
        self.assertEqual(response.data["entitlement"]["product"], "zgodomat")
        self.assertEqual(response.data["entitlement"]["plan"], "pilot")

    def test_oauth_bearer_can_read_me_and_access_context(self):
        self.bearer()

        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["id"], str(self.user.pk))

        response = self.client.get(
            "/api/v1/access-context/",
            {"organization_id": str(self.org.pk), "product": "zgodomat"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["entitlement"]["product"], "zgodomat")

    def test_oauth_bearer_without_qm_access_scope_is_denied_context(self):
        self.bearer(scope="openid profile email")
        response = self.client.get(
            "/api/v1/access-context/",
            {"organization_id": str(self.org.pk), "product": "zgodomat"},
        )
        self.assertEqual(response.status_code, 403)

    def test_cross_tenant_context_is_hidden(self):
        self.login()
        response = self.client.get(
            "/api/v1/access-context/",
            {"organization_id": str(self.other_org.pk), "product": "zgodomat"},
        )
        self.assertEqual(response.status_code, 404)

    def test_missing_entitlement_is_denied(self):
        self.entitlement.delete()
        self.login()
        response = self.client.get(
            "/api/v1/access-context/",
            {"organization_id": str(self.org.pk), "product": "zgodomat"},
        )
        self.assertEqual(response.status_code, 403)

    def test_expired_entitlement_is_denied(self):
        self.entitlement.valid_until = timezone.now() - timedelta(seconds=1)
        self.entitlement.save(update_fields=["valid_until"])
        self.login()
        response = self.client.get(
            "/api/v1/access-context/",
            {"organization_id": str(self.org.pk), "product": "zgodomat"},
        )
        self.assertEqual(response.status_code, 403)

    def test_suspended_user_session_becomes_unauthenticated(self):
        self.login()
        self.user.status = User.Status.SUSPENDED
        self.user.save(update_fields=["status"])

        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 401)

    def test_suspended_user_cannot_reauthenticate(self):
        self.user.status = User.Status.SUSPENDED
        self.user.save(update_fields=["status"])
        authenticated = authenticate(
            email=self.user.email,
            password="correct horse battery staple",
        )
        self.assertIsNone(authenticated)

    def test_suspended_membership_is_hidden(self):
        self.membership.status = Membership.Status.SUSPENDED
        self.membership.save(update_fields=["status"])
        self.login()
        response = self.client.get(
            "/api/v1/access-context/",
            {"organization_id": str(self.org.pk), "product": "zgodomat"},
        )
        self.assertEqual(response.status_code, 404)
