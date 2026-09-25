import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductEntitlement",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("product_id", models.SlugField(max_length=64)),
                ("plan", models.CharField(blank=True, default="", max_length=64)),
                ("status", models.CharField(choices=[("active", "Active"), ("suspended", "Suspended"), ("cancelled", "Cancelled")], default="active", max_length=16)),
                ("valid_from", models.DateTimeField(blank=True, null=True)),
                ("valid_until", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="entitlements", to="organizations.organization")),
            ],
        ),
        migrations.AddConstraint(
            model_name="productentitlement",
            constraint=models.UniqueConstraint(fields=("organization", "product_id"), name="uq_entitlement_org_product"),
        ),
    ]
