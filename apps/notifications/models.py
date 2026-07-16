from django.conf import settings
from django.db import models
from django.utils import timezone


class NotificationType(models.TextChoices):
    INFO = "INFO", "Info"
    SUCCESS = "SUCCESS", "Success"
    WARNING = "WARNING", "Warning"
    ERROR = "ERROR", "Error"

    BOOKING = "BOOKING", "Booking"
    ATTENDANCE = "ATTENDANCE", "Attendance"
    SELF_PRACTICE = "SELF_PRACTICE", "Self-Practice"
    OSCE = "OSCE", "OSCE"
    INVENTORY = "INVENTORY", "Inventory"
    REPORT = "REPORT", "Report"
    ACCOUNT = "ACCOUNT", "Account"


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="notifications_sent",
        null=True,
        blank=True,
    )
    notification_type = models.CharField(
        max_length=40,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        db_index=True,
    )
    title = models.CharField(max_length=180)
    message = models.TextField()
    url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["created_at"]),
        ]

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    def __str__(self):
        return f"{self.recipient} - {self.title}"


class AnnouncementAudience(models.TextChoices):
    ALL = "ALL", "All users"
    STUDENTS = "STUDENTS", "Students"
    STAFF = "STAFF", "Staff"
    LECTURERS = "LECTURERS", "Lecturers"
    ADMINISTRATION = "ADMINISTRATION", "Administration"


class Announcement(models.Model):
    title = models.CharField(max_length=180)
    message = models.TextField()
    audience = models.CharField(
        max_length=40,
        choices=AnnouncementAudience.choices,
        default=AnnouncementAudience.ALL,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="announcements_created",
        null=True,
        blank=True,
    )
    published_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title