from .models import AuditEvent


def record_oauth_event(
    request,
    event_type,
    *,
    target_type="",
    target_id="",
    organization_id=None,
    product_id="",
    metadata=None,
):
    token = getattr(request, "auth", None)
    return AuditEvent.objects.create(
        event_type=event_type,
        actor_type=AuditEvent.ActorType.OAUTH_CLIENT,
        oauth_client_id=str(getattr(token, "application_id", "") or ""),
        target_type=target_type,
        target_id=str(target_id or ""),
        organization_id=organization_id,
        product_id=product_id,
        metadata_json=metadata or {},
    )


def record_admin_event(
    request,
    event_type,
    obj,
    *,
    metadata=None,
):
    organization_id = getattr(obj, "organization_id", None)
    product_id = getattr(obj, "product_id", "") or ""
    target_user_id = getattr(obj, "user_id", None)

    payload = dict(metadata or {})
    if target_user_id:
        payload.setdefault("target_user_id", str(target_user_id))

    return AuditEvent.objects.create(
        event_type=event_type,
        actor_type=AuditEvent.ActorType.USER,
        actor_user=request.user if request.user.is_authenticated else None,
        target_type=obj._meta.label_lower,
        target_id=str(obj.pk),
        organization_id=organization_id,
        product_id=product_id,
        metadata_json=payload,
    )
