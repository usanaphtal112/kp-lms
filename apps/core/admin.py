from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "actor",
        "action",
        "app_label",
        "model_name",
        "object_repr",
        "ip_address",
    ]
    list_filter = [
        "action",
        "app_label",
        "model_name",
        "created_at",
    ]
    search_fields = [
        "actor__username",
        "object_repr",
        "message",
        "path",
        "ip_address",
    ]
    readonly_fields = [
        "actor",
        "action",
        "app_label",
        "model_name",
        "object_id",
        "object_repr",
        "target_content_type",
        "target_object_id",
        "message",
        "old_values",
        "new_values",
        "metadata",
        "ip_address",
        "user_agent",
        "path",
        "request_method",
        "created_at",
    ]

    def has_add_permission(self, request):
        return False