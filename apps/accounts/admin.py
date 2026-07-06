from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import AccountActionLog, StaffProfile, StudentProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = [
        "username",
        "first_name",
        "last_name",
        "role",
        "email",
        "is_active",
        "must_change_password",
        "is_staff",
    ]
    list_filter = [
        "role",
        "is_active",
        "must_change_password",
        "is_staff",
        "is_superuser",
    ]
    search_fields = [
        "username",
        "first_name",
        "last_name",
        "email",
        "student_profile__registration_number",
        "staff_profile__staff_number",
    ]

    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "KP-HSLMS account details",
            {
                "fields": (
                    "role",
                    "phone_number",
                    "must_change_password",
                )
            },
        ),
    )

    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (
            "KP-HSLMS account details",
            {
                "fields": (
                    "role",
                    "phone_number",
                    "must_change_password",
                )
            },
        ),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = [
        "registration_number",
        "user",
        "student_type",
        "academic_status",
        "current_academic_level",
        "is_active_student",
    ]
    list_filter = [
        "student_type",
        "academic_status",
        "current_academic_level",
        "is_active_student",
    ]
    search_fields = [
        "registration_number",
        "user__username",
        "user__first_name",
        "user__last_name",
    ]


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "staff_number",
        "job_title",
        "department_name",
    ]
    search_fields = [
        "staff_number",
        "user__username",
        "user__first_name",
        "user__last_name",
        "department_name",
    ]


@admin.register(AccountActionLog)
class AccountActionLogAdmin(admin.ModelAdmin):
    list_display = [
        "target_user",
        "action",
        "actor",
        "created_at",
    ]
    list_filter = [
        "action",
        "created_at",
    ]
    search_fields = [
        "target_user__username",
        "actor__username",
        "message",
    ]
    readonly_fields = [
        "actor",
        "target_user",
        "action",
        "message",
        "metadata",
        "created_at",
    ]

    def has_add_permission(self, request):
        return False