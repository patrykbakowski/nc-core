from datetime import timedelta
import uuid

from django.contrib.auth import authenticate, get_user_model
from django.test import TestCase
from django.utils import timezone
from oauth2_provider.models import get_access_token_model, get_application_model
from rest_framework.test import APIClient

from audit.models import AuditEvent
from entitlements.models import (
    OAuthClientPolicy,
    OAuthClientProductGrant,
    ProductEntitlement,
)
from organizations.models import Membership, Organization

User = get_user_model()
Application = get_application_model()
AccessToken = get_access_token_model()


class OIDCProviderTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_discovery_and_jwks_are_live(self):
        discovery = self.client.get("/o/.well-known/openid-configuration")
        self.assertEqual(discovery.status_code, 200)
        payload = discovery.json()
        self.assertEqual(payload["issuer"], "https://identity.test/o")
        self.assertIn("authorization_endpoint", payload)
        self.assertIn("token_endpoint", payload)
        self.assertIn("jwks_uri", payload)

        jwks = self.client.get("/o/.well-known/jwks.json")
        self.assertEqual(jwks.status_code, 200)
        self.assertTrue(jwks.json()["keys"])


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

    def _policy(
        self,
        application,
        products=("zgodomat",),
        can_provision_accounts=False,
    ):
        policy = OAuthClientPolicy.objects.create(
            application_client_id=application.client_id,
            name=application.name,
            can_provision_accounts=can_provision_accounts,
        )
        for product in products:
            OAuthClientProductGrant.objects.create(
                client_policy=policy,
                product_id=product,
            )
        return policy

    def login(self):
        return self.client.post(
            "/api/v1/auth/login/",
            {"email": self.user.email, "password": "correct horse battery staple"},
            format="json",
        )

    def bearer(
        self,
        scope="openid profile email qm.access",
        products=("zgodomat",),
        with_policy=True,
    ):
        application = Application.objects.create(
            user=self.user,
            name="QM test client",
            client_type="confidential",
            authorization_grant_type="authorization-code",
            redirect_uris="https://client.example/callback",
        )
        if with_policy:
            self._policy(application, products=products)
        token = AccessToken.objects.create(
            user=self.user,
            application=application,
            token=f"test-token-{uuid.uuid4()}",
            expires=timezone.now() + timedelta(minutes=10),
            scope=scope,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.token}")
        return token

    def service_token(
        self,
        scope="qm.access",
        products=("zgodomat",),
        with_policy=True,
        can_provision_accounts=False,
    ):
        application = Application.objects.create(
            name="QM service test",
            client_type="confidential",
            authorization_grant_type="client-credentials",
        )
        if with_policy:
            self._policy(
                application,
                products=products,
                can_provision_accounts=can_provision_accounts,
            )
        token = AccessToken.objects.create(
            user=None,
            application=application,
            token=f"service-token-{uuid.uuid4()}",
            expires=timezone.now() + timedelta(minutes=10),
            scope=scope,
        )
        self.client.force_authenticate(token=token)
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
        self.assertEqual(len(response.data["memberships"]), 1)

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

    def test_oauth_me_without_qm_access_scope_hides_memberships(self):
        self.bearer(scope="openid profile email")
        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["memberships"], [])

    def test_oauth_client_without_policy_is_denied_context(self):
        self.bearer(with_policy=False)
        response = self.client.get(
            "/api/v1/access-context/",
            {"organization_id": str(self.org.pk), "product": "zgodomat"},
        )
        self.assertEqual(response.status_code, 403)

    def test_oauth_client_cannot_cross_product_boundary(self):
        ProductEntitlement.objects.create(
            organization=self.org,
            product_id="neuroconnect",
        )
        self.bearer(products=("zgodomat",))
        response = self.client.get(
            "/api/v1/access-context/",
            {"organization_id": str(self.org.pk), "product": "neuroconnect"},
        )
        self.assertEqual(response.status_code, 403)

    def test_oauth_me_only_exposes_orgs_for_allowed_products(self):
        nc_org = Organization.objects.create(name="NC", slug="nc")
        Membership.objects.create(
            organization=nc_org,
            user=self.user,
            role=Membership.Role.ADMIN,
        )
        ProductEntitlement.objects.create(
            organization=nc_org,
            product_id="neuroconnect",
        )

        self.bearer(products=("zgodomat",))
        response = self.client.get("/api/v1/auth/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["organization"]["slug"] for item in response.data["memberships"]],
            ["acme"],
        )

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

    def test_service_access_context_for_known_user(self):
        self.service_token()
        response = self.client.get(
            "/api/v1/service/access-context/",
            {
                "user_id": str(self.user.pk),
                "organization_id": str(self.org.pk),
                "product": "zgodomat",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["id"], str(self.user.pk))
        self.assertEqual(response.data["membership"]["role"], Membership.Role.ADMIN)

    def test_service_access_context_requires_qm_access_scope(self):
        self.service_token(scope="qm.provision")
        response = self.client.get(
            "/api/v1/service/access-context/",
            {
                "user_id": str(self.user.pk),
                "organization_id": str(self.org.pk),
                "product": "zgodomat",
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_service_client_cannot_cross_product_boundary(self):
        ProductEntitlement.objects.create(
            organization=self.org,
            product_id="neuroconnect",
        )
        self.service_token(products=("zgodomat",))
        response = self.client.get(
            "/api/v1/service/access-context/",
            {
                "user_id": str(self.user.pk),
                "organization_id": str(self.org.pk),
                "product": "neuroconnect",
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_service_access_context_hides_suspended_user(self):
        self.user.status = User.Status.SUSPENDED
        self.user.save(update_fields=["status"])
        self.service_token()
        response = self.client.get(
            "/api/v1/service/access-context/",
            {
                "user_id": str(self.user.pk),
                "organization_id": str(self.org.pk),
                "product": "zgodomat",
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_provision_requires_explicit_client_policy_flag(self):
        self.service_token(
            scope="qm.provision",
            can_provision_accounts=False,
        )
        response = self.client.post(
            "/api/v1/accounts/invitations/",
            {"email": "new-user@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_provision_allowed_for_explicitly_authorized_client(self):
        self.service_token(
            scope="qm.provision",
            can_provision_accounts=True,
        )
        response = self.client.post(
            "/api/v1/accounts/invitations/",
            {"email": "new-user@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["state"], "pending")
        self.assertTrue(response.data["invitation_sent"])
        event = AuditEvent.objects.get(event_type="identity.invitation.created")
        self.assertEqual(event.actor_type, AuditEvent.ActorType.OAUTH_CLIENT)
        self.assertEqual(event.target_id, response.data["user"]["id"])
        self.assertTrue(event.oauth_client_id)
