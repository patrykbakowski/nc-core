from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac

from .models import AuthThrottleBucket


@dataclass(frozen=True)
class ThrottleResult:
    allowed: bool
    retry_after: int


def _client_ip(request):
    cf_ip = (request.META.get("HTTP_CF_CONNECTING_IP") or "").strip()
    if cf_ip:
        return cf_ip

    forwarded = (request.META.get("HTTP_X_FORWARDED_FOR") or "").strip()
    if forwarded:
        return forwarded.split(",", 1)[0].strip()

    return (request.META.get("REMOTE_ADDR") or "unknown").strip()


def _key_hash(scope, request, identifier):
    normalized = (identifier or "").strip().lower()
    material = f"{_client_ip(request)}|{normalized}"
    return salted_hmac(
        f"qm_identity.auth_throttle.{scope}",
        material,
        secret=settings.SECRET_KEY,
        algorithm="sha256",
    ).hexdigest()


def consume_auth_attempt(request, scope, identifier, *, limit, window_seconds):
    """Consume one fixed-window attempt shared across all Gunicorn workers."""

    now = timezone.now()
    window = timedelta(seconds=window_seconds)
    key_hash = _key_hash(scope, request, identifier)

    with transaction.atomic():
        bucket, _ = (
            AuthThrottleBucket.objects.select_for_update()
            .get_or_create(
                scope=scope,
                key_hash=key_hash,
                defaults={
                    "window_started_at": now,
                    "count": 0,
                },
            )
        )

        if bucket.window_started_at <= now - window:
            bucket.window_started_at = now
            bucket.count = 0

        elapsed = (now - bucket.window_started_at).total_seconds()
        retry_after = max(1, int(window_seconds - elapsed))

        if bucket.count >= limit:
            return ThrottleResult(False, retry_after)

        bucket.count += 1
        bucket.save(
            update_fields=["window_started_at", "count", "updated_at"]
        )

    return ThrottleResult(True, 0)
