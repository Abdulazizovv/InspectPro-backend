def log_activity(user, action, target=None, request=None, metadata=None):
    """
    Xodim faoliyatini ActivityLog ga yozadi.

    :param user: accounts.User instance
    :param action: ActivityLog.Action tanlovidan biri
    :param target: model instance (Vehicle, Client, Inspection, ...)
    :param request: DRF Request (IP olish uchun)
    :param metadata: qo'shimcha ma'lumotlar dict
    """
    from apps.accounts.models import ActivityLog

    ip = None
    if request:
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = x_forwarded.split(",")[0].strip() if x_forwarded else request.META.get("REMOTE_ADDR")

    ActivityLog.objects.create(
        user=user,
        branch=getattr(user, "branch", None),
        action=action,
        target_type=type(target).__name__ if target else "",
        target_id=str(target.pk) if target else "",
        target_repr=str(target)[:255] if target else "",
        metadata=metadata or {},
        ip_address=ip,
    )
