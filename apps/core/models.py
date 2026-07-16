from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AuditAction(models.TextChoices):
    CREATE = "CREATE", "Create"
    UPDATE = "UPDATE", "Update"
    DELETE = "DELETE", "Delete"
    VIEW = "VIEW", "View"
    DOWNLOAD = "DOWNLOAD", "Download"
    APPROVE = "APPROVE", "Approve"
    REJECT = "REJECT", "Reject"
    PUBLISH = "PUBLISH", "Publish"
    LOGIN = "LOGIN", "Login"
    LOGOUT = "LOGOUT", "Logout"
    PASSWORD_RESET = "PASSWORD_RESET", "Password Reset"
    PERMISSION_CHANGE = "PERMISSION_CHANGE", "Permission Change"
    MARK_CHANGE = "MARK_CHANGE", "Mark Change"
    ATTENDANCE_CHANGE = "ATTENDANCE_CHANGE", "Attendance Change"


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        null=True,
        blank=True,
    )
    action = models.CharField(
        max_length=40,
        choices=AuditAction.choices,
        db_index=True,
    )
    app_label = models.CharField(max_length=80, blank=True)
    model_name = models.CharField(max_length=120, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)

    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    target_object_id = models.CharField(max_length=100, blank=True)
    target_object = GenericForeignKey(
        "target_content_type",
        "target_object_id",
    )

    message = models.TextField(blank=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    path = models.CharField(max_length=255, blank=True)
    request_method = models.CharField(max_length=12, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["app_label", "model_name"]),
        ]

    def __str__(self):
        return f"{self.actor} - {self.action} - {self.object_repr}"