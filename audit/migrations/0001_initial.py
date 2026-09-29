import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                ("event_type", models.CharField(max_length=96)),
                ("actor_type", models.CharField(choices=[("user", "User"), ("oauth_client", "OAuth client"), ("system", "System")], max_length=24)),
                ("oauth_client_id", models.CharField(blank=True, default="", max_length=255)),
                ("target_type", models.CharField(blank=True, default="", max_length=96)),
                ("target_id", models.CharField(blank=True, default="", max_length=255)),
                ("organization_id", models.UUIDField(blank=True, null=True)),
                ("product_id", models.SlugField(blank=True, default="", max_length=64)),
                ("metadata_json", models.JSONField(blank=True, default=dict)),
                ("actor_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="identity_audit_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-occurred_at",)},
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(fields=["event_type", "occurred_at"], name="audit_audit_event_t_65aba1_idx"),
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(fields=["oauth_client_id", "occurred_at"], name="audit_audit_oauth_c_61d91a_idx"),
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(fields=["organization_id", "occurred_at"], name="audit_audit_organiz_eb1fe8_idx"),
        ),
    ]
