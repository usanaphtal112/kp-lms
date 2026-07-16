def notifications_context(request):
    if not request.user.is_authenticated:
        return {
            "unread_notifications_count": 0,
            "recent_notifications": [],
        }

    queryset = request.user.notifications.all()

    return {
        "unread_notifications_count": queryset.filter(is_read=False).count(),
        "recent_notifications": queryset[:5],
    }