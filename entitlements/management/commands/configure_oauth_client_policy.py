from django.core.management.base import BaseCommand, CommandError
from oauth2_provider.models import get_application_model

from entitlements.models import OAuthClientPolicy, OAuthClientProductGrant


Application = get_application_model()


class Command(BaseCommand):
    help = "Configure least-privilege QM policy for an existing OAuth/OIDC client."

    def add_arguments(self, parser):
        parser.add_argument("client_id")
        parser.add_argument("--name", default="")
        parser.add_argument(
            "--product",
            action="append",
            default=[],
            help="Add an allowed product slug. May be repeated.",
        )
        provisioning = parser.add_mutually_exclusive_group()
        provisioning.add_argument("--enable-provision", action="store_true")
        provisioning.add_argument("--disable-provision", action="store_true")
        active = parser.add_mutually_exclusive_group()
        active.add_argument("--activate", action="store_true")
        active.add_argument("--deactivate", action="store_true")

    def handle(self, *args, **options):
        client_id = options["client_id"].strip()
        application = Application.objects.filter(client_id=client_id).first()
        if application is None:
            raise CommandError("OAuth application with this client_id does not exist.")

        policy, created = OAuthClientPolicy.objects.get_or_create(
            application_client_id=client_id,
            defaults={
                "name": options["name"] or application.name,
                "is_active": True,
            },
        )

        changed = []
        if options["name"] and policy.name != options["name"]:
            policy.name = options["name"]
            changed.append("name")
        elif not policy.name and application.name:
            policy.name = application.name
            changed.append("name")

        if options["enable_provision"] and not policy.can_provision_accounts:
            policy.can_provision_accounts = True
            changed.append("can_provision_accounts")
        elif options["disable_provision"] and policy.can_provision_accounts:
            policy.can_provision_accounts = False
            changed.append("can_provision_accounts")

        if options["activate"] and not policy.is_active:
            policy.is_active = True
            changed.append("is_active")
        elif options["deactivate"] and policy.is_active:
            policy.is_active = False
            changed.append("is_active")

        if changed:
            policy.save(update_fields=changed + ["updated_at"])

        granted = []
        for product in options["product"]:
            product = product.strip()
            if not product:
                continue
            _, grant_created = OAuthClientProductGrant.objects.get_or_create(
                client_policy=policy,
                product_id=product,
            )
            if grant_created:
                granted.append(product)

        self.stdout.write(
            self.style.SUCCESS(
                "OAuth client policy configured: "
                f"created={created}, active={policy.is_active}, "
                f"can_provision_accounts={policy.can_provision_accounts}, "
                f"new_product_grants={granted}"
            )
        )
