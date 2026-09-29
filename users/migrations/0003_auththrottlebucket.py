import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_externalidentity"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuthThrottleBucket",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("scope", models.CharField(max_length=32)),
                ("key_hash", models.CharField(max_length=64)),
                ("window_started_at", models.DateTimeField()),
                ("count", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name="auththrottlebucket",
            constraint=models.UniqueConstraint(
                fields=("scope", "key_hash"),
                name="uq_auth_throttle_scope_key",
            ),
        ),
        migrations.AddIndex(
            model_name="auththrottlebucket",
            index=models.Index(
                fields=["scope", "window_started_at"],
                name="auth_throttle_scope_window_idx",
            ),
        ),
    ]
