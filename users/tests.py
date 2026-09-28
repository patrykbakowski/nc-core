import uuid

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import ExternalIdentity

User = get_user_model()


class IdentityModelTests(TestCase):
    def test_user_is_uuid_email_native(self):
        user = User.objects.create_user(
            email="Person@Example.COM",
            password="correct horse battery staple",
        )
        self.assertIsInstance(user.pk, uuid.UUID)
        self.assertEqual(user.email, "person@example.com")
        self.assertFalse(hasattr(user, "username"))

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
