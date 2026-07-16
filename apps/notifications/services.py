from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import UserRole

from .models import AnnouncementAudience, Notification, NotificationType


def notify_user(*, recipient, title, message, notification_type=NotificationType.INFO, actor=None, url=""):
    if not recipient or not recipient.is_active:
        return None

    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        notification_type=notification_type,
        title=title,
        message=message,
        url=url,
    )


def notify_users(*, recipients, title, message, notification_type=NotificationType.INFO, actor=None, url=""):
    notifications = []

    for recipient in recipients:
        notification = notify_user(
            recipient=recipient,
            actor=actor,
            title=title,
            message=message,
            notification_type=notification_type,
            url=url,
        )
        if notification:
            notifications.append(notification)

    return notifications


def notify_role(*, role, title, message, notification_type=NotificationType.INFO, actor=None, url=""):
    User = get_user_model()

    recipients = User.objects.filter(
        role=role,
        is_active=True,
    )

    return notify_users(
        recipients=recipients,
        actor=actor,
        title=title,
        message=message,
        notification_type=notification_type,
        url=url,
    )


def notify_admins(*, title, message, notification_type=NotificationType.INFO, actor=None, url=""):
    User = get_user_model()

    recipients = User.objects.filter(
        role__in=[
            UserRole.IT_ADMIN,
            UserRole.ADMINISTRATION,
        ],
        is_active=True,
    )

    return notify_users(
        recipients=recipients,
        actor=actor,
        title=title,
        message=message,
        notification_type=notification_type,
        url=url,
    )


def get_recipients_for_announcement(audience):
    User = get_user_model()

    base = User.objects.filter(is_active=True)

    if audience == AnnouncementAudience.ALL:
        return base

    if audience == AnnouncementAudience.STUDENTS:
        return base.filter(role=UserRole.STUDENT)

    if audience == AnnouncementAudience.LECTURERS:
        return base.filter(role=UserRole.LECTURER)

    if audience == AnnouncementAudience.ADMINISTRATION:
        return base.filter(role__in=[UserRole.IT_ADMIN, UserRole.ADMINISTRATION])

    if audience == AnnouncementAudience.STAFF:
        return base.exclude(role=UserRole.STUDENT)

    return base.none()