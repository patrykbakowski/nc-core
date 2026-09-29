import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("entitlements", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="OAuthClientPolicy",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "application_client_id",
                    models.CharField(max_length=255, unique=True),
                ),
                ("name", models.CharField(blank=True, default="", max_length=200)),
                ("is_active", models.BooleanField(default=True)),
                ("can_provision_accounts", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="OAuthClientProductGrant",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("product_id", models.SlugField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "client_policy",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="product_grants",
                        to="entitlements.oauthclientpolicy",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="oauthclientproductgrant",
            constraint=models.UniqueConstraint(
                fields=("client_policy", "product_id"),
                name="uq_oauth_client_policy_product",
            ),
        ),
    ]
