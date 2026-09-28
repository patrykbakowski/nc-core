from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from entitlements.models import (
    OAuthClientPolicy,
    ProductEntitlement,
)


def oauth_client_id(request):
    token = getattr(request, "auth", None)
    application = getattr(token, "application", None)
    return (getattr(application, "client_id", "") or "").strip()


def active_oauth_client_policy(request):
    client_id = oauth_client_id(request)
    if not client_id:
        return None
    return (
        OAuthClientPolicy.objects
        .prefetch_related("product_grants")
        .filter(application_client_id=client_id, is_active=True)
        .first()
    )


def oauth_client_has_policy(request):
    return active_oauth_client_policy(request) is not None


def oauth_client_can_provision(request):
    policy = active_oauth_client_policy(request)
    return bool(policy and policy.can_provision_accounts)


def require_oauth_client_product(request, product_id):
    """Sessions are trusted central UI calls; OAuth tokens need an explicit product grant."""

    if getattr(request, "auth", None) is None:
        return

    policy = active_oauth_client_policy(request)
    if not policy or not policy.allows_product(product_id):
        raise PermissionDenied("OAuth client is not allowed to access this product.")


def oauth_client_allowed_products(request):
    """Return None for central sessions, otherwise the token application's product allowlist."""

    if getattr(request, "auth", None) is None:
        return None

    policy = active_oauth_client_policy(request)
    if not policy:
        raise PermissionDenied("OAuth client policy is missing or inactive.")
    return list(policy.product_grants.values_list("product_id", flat=True))


def active_entitled_organization_ids(product_ids):
    now = timezone.now()
    return (
        ProductEntitlement.objects
        .filter(
            product_id__in=product_ids,
            status=ProductEntitlement.Status.ACTIVE,
            organization__status="active",
        )
        .filter(Q(valid_from__isnull=True) | Q(valid_from__lte=now))
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gt=now))
        .values_list("organization_id", flat=True)
    )
