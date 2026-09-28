import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_datetime

from entitlements.models import ProductEntitlement
from organizations.models import Membership, Organization
from users.models import ExternalIdentity, User


ROLE_MAP = {
    "owner": Membership.Role.OWNER,
    "admin": Membership.Role.ADMIN,
    "member": Membership.Role.MEMBER,
    "viewer": Membership.Role.VIEWER,
    Membership.Role.OWNER: Membership.Role.OWNER,
    Membership.Role.ADMIN: Membership.Role.ADMIN,
    Membership.Role.MEMBER: Membership.Role.MEMBER,
    Membership.Role.VIEWER: Membership.Role.VIEWER,
}


def _dt(value):
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        raise CommandError(f"Invalid datetime in identity snapshot: {value!r}")
    return parsed


class Command(BaseCommand):
    help = "Import a one-time QM Identity snapshot while preserving UUIDs and password hashes."

    def add_arguments(self, parser):
        parser.add_argument("snapshot", type=Path)
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate/import inside a transaction and roll it back.",
        )

    def handle(self, *args, **options):
        path = options["snapshot"]
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Cannot read identity snapshot: {exc}") from exc

        required = {"users", "organizations", "memberships", "entitlements", "external_identities"}
        missing = required.difference(payload)
        if missing:
            raise CommandError(f"Identity snapshot missing keys: {', '.join(sorted(missing))}")

        if any(
            model.objects.exists()
            for model in (User, Organization, Membership, ProductEntitlement, ExternalIdentity)
        ):
            raise CommandError("Target identity database is not empty; refusing snapshot import.")

        with transaction.atomic():
            for row in payload["users"]:
                user = User(
                    id=row["id"],
                    email=row["email"],
                    password=row["password_hash"],
                    first_name=row.get("first_name", ""),
                    last_name=row.get("last_name", ""),
                    is_active=bool(row.get("is_active", True)),
                    is_staff=bool(row.get("is_staff", False)),
                    is_superuser=bool(row.get("is_superuser", False)),
                    status=(
                        User.Status.ACTIVE
                        if row.get("is_active", True)
                        else User.Status.SUSPENDED
                    ),
                )
                if row.get("date_joined"):
                    user.date_joined = _dt(row["date_joined"])
                user.last_login = _dt(row.get("last_login"))
                user.save(force_insert=True)

            for row in payload["organizations"]:
                status = row.get("status", Organization.Status.ACTIVE)
                if status == "inactive":
                    status = Organization.Status.SUSPENDED
                Organization.objects.create(
                    id=row["id"],
                    name=row["name"],
                    slug=row["slug"],
                    status=status,
                )

            for row in payload["memberships"]:
                role = ROLE_MAP.get(row["role"])
                if role is None:
                    raise CommandError(f"Unsupported legacy membership role: {row['role']!r}")
                status = row.get("status")
                if not status:
                    status = (
                        Membership.Status.ACTIVE
                        if row.get("is_active", True)
                        else Membership.Status.SUSPENDED
                    )
                Membership.objects.create(
                    id=row["id"],
                    organization_id=row["organization_id"],
                    user_id=row["user_id"],
                    role=role,
                    status=status,
                )

            for row in payload["entitlements"]:
                status = row.get("status")
                if not status:
                    status = (
                        ProductEntitlement.Status.ACTIVE
                        if row.get("is_active", True)
                        else ProductEntitlement.Status.SUSPENDED
                    )
                ProductEntitlement.objects.create(
                    id=row["id"],
                    organization_id=row["organization_id"],
                    product_id=row.get("product_id") or row["product"],
                    plan=row.get("plan", ""),
                    status=status,
                    valid_from=_dt(row.get("valid_from")),
                    valid_until=_dt(row.get("valid_until")),
                )

            for row in payload["external_identities"]:
                ExternalIdentity.objects.create(
                    id=row["id"],
                    user_id=row["user_id"],
                    provider=row["provider"],
                    external_subject=row["external_subject"],
                    metadata_json=row.get("metadata_json", {}),
                )

            counts = {
                "users": User.objects.count(),
                "organizations": Organization.objects.count(),
                "memberships": Membership.objects.count(),
                "entitlements": ProductEntitlement.objects.count(),
                "external_identities": ExternalIdentity.objects.count(),
            }

            if options["dry_run"]:
                transaction.set_rollback(True)

        mode = "validated (rolled back)" if options["dry_run"] else "imported"
        self.stdout.write(self.style.SUCCESS(f"Identity snapshot {mode}: {counts}"))
