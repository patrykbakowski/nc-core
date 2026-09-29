import json
import tempfile
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings

from entitlements.models import ProductEntitlement
from organizations.models import Membership, Organization
from .models import AuthThrottleBucket, ExternalIdentity

User = get_user_model()


class IdentityModelTests(TestCase):
    def test_user_is_uuid_email_native(self):
        user = User.objects.create_user(
            email="Person@Example.COM",
            password="correct horse battery staple",
        )
        self.assertIsInstance(user.pk, uuid.UUID)
        self.assertEqual(user.email, "person@example.com")
        self.assertNotIn("username", {field.name for field in user._meta.get_fields()})

    def test_external_identity_subject_is_unique_per_provider(self):
        first = User.objects.create_user(email="first@example.com", password="password 12345")
        second = User.objects.create_user(email="second@example.com", password="password 12345")

        ExternalIdentity.objects.create(
            user=first,
            provider="wordpress",
            external_subject="123",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            ExternalIdentity.objects.create(
                user=second,
                provider="wordpress",
                external_subject="123",
            )

        ExternalIdentity.objects.create(
            user=second,
            provider="google",
            external_subject="123",
        )


class IdentitySnapshotImportTests(TestCase):
    def test_import_preserves_ids_password_and_access_mapping(self):
        user_id = uuid.uuid4()
        organization_id = uuid.uuid4()
        membership_id = uuid.uuid4()
        entitlement_id = uuid.uuid4()
        external_id = uuid.uuid4()
        payload = {
            "users": [
                {
                    "id": str(user_id),
                    "email": "Legacy@Example.COM",
                    "password_hash": make_password("legacy password 123"),
                    "first_name": "Legacy",
                    "last_name": "User",
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                    "date_joined": "2026-09-01T10:00:00+00:00",
                    "last_login": None,
                }
            ],
            "organizations": [
                {
                    "id": str(organization_id),
                    "name": "Legacy Org",
                    "slug": "legacy-org",
                    "status": "active",
                }
            ],
            "memberships": [
                {
                    "id": str(membership_id),
                    "organization_id": str(organization_id),
                    "user_id": str(user_id),
                    "role": "admin",
                    "is_active": True,
                }
            ],
            "entitlements": [
                {
                    "id": str(entitlement_id),
                    "organization_id": str(organization_id),
                    "product": "zgodomat",
                    "is_active": True,
                    "valid_from": None,
                    "valid_until": None,
                }
            ],
            "external_identities": [
                {
                    "id": str(external_id),
                    "user_id": str(user_id),
                    "provider": "wordpress",
                    "external_subject": "42",
                    "metadata_json": {},
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as snapshot:
            json.dump(payload, snapshot)
            snapshot.flush()
            call_command("import_identity_snapshot", snapshot.name)

        user = User.objects.get(pk=user_id)
        self.assertEqual(user.email, "legacy@example.com")
        self.assertTrue(user.check_password("legacy password 123"))
        self.assertEqual(
            Membership.objects.get(pk=membership_id).role,
            Membership.Role.ADMIN,
        )
        self.assertEqual(
            ProductEntitlement.objects.get(pk=entitlement_id).product_id,
            "zgodomat",
        )
        self.assertEqual(
            ExternalIdentity.objects.get(pk=external_id).external_subject,
            "42",
        )
        self.assertEqual(Organization.objects.get(pk=organization_id).slug, "legacy-org")



class AuthThrottleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="login@example.com",
            password="correct horse battery staple",
        )

    @override_settings(
        QM_LOGIN_RATE_LIMIT=2,
        QM_LOGIN_RATE_WINDOW_SECONDS=300,
    )
    def test_browser_login_is_throttled_across_attempts(self):
        for _ in range(2):
            response = self.client.post(
                "/accounts/login/",
                {"username": self.user.email, "password": "wrong password"},
                REMOTE_ADDR="203.0.113.10",
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/accounts/login/",
            {"username": self.user.email, "password": "wrong password"},
            REMOTE_ADDR="203.0.113.10",
        )
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response.headers)
        self.assertEqual(
            AuthThrottleBucket.objects.filter(scope="login").count(),
            1,
        )

    @override_settings(
        QM_PASSWORD_RESET_RATE_LIMIT=2,
        QM_PASSWORD_RESET_RATE_WINDOW_SECONDS=900,
    )
    def test_password_reset_is_throttled_without_account_enumeration(self):
        for _ in range(2):
            response = self.client.post(
                "/accounts/password-reset/",
                {"email": "missing@example.com"},
                REMOTE_ADDR="203.0.113.11",
            )
            self.assertEqual(response.status_code, 302)

        response = self.client.post(
            "/accounts/password-reset/",
            {"email": "missing@example.com"},
            REMOTE_ADDR="203.0.113.11",
        )
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response.headers)
