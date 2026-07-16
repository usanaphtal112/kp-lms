from django.contrib.contenttypes.models import ContentType

from .models import AuditAction, AuditLog


def get_client_ip(request):
    if not request:
        return None

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def log_audit(
    *,
    actor=None,
    action,
    target_object=None,
    message="",
    old_values=None,
    new_values=None,
    metadata=None,
    request=None,
):
    content_type = None
    app_label = ""
    model_name = ""
    object_id = ""
    object_repr = ""

    if target_object is not None:
        content_type = ContentType.objects.get_for_model(
            target_object,
            for_concrete_model=False,
        )
        app_label = target_object._meta.app_label
        model_name = target_object._meta.model_name
        object_id = str(target_object.pk)
        object_repr = str(target_object)[:255]

    return AuditLog.objects.create(
        actor=actor,
        action=action,
        app_label=app_label,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        target_content_type=content_type,
        target_object_id=object_id,
        message=message,
        old_values=old_values or {},
        new_values=new_values or {},
        metadata=metadata or {},
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
        path=request.path if request else "",
        request_method=request.method if request else "",
    )