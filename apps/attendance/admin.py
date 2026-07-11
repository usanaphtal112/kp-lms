from django.contrib import admin

from .models import (
    AttendanceChangeLog,
    AttendanceRecord,
    EligibilitySnapshot,
    SelfPracticeAttendanceRecord,
)

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "demonstration_session",
        "status",
        "recorded_by",
        "recorded_at",
    ]
    list_filter = [
        "status",
        "demonstration_session__module_offering__academic_year",
        "demonstration_session__module_offering__semester",
    ]
    search_fields = [
        "student__username",
        "student__first_name",
        "student__last_name",
        "student__student_profile__registration_number",
        "demonstration_session__topic",
    ]
    autocomplete_fields = [
        "student",
        "demonstration_session",
        "recorded_by",
    ]


@admin.register(EligibilitySnapshot)
class EligibilitySnapshotAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "module_offering",
        "attendance_percentage",
        "is_self_practice_eligible",
        "is_osce_eligible",
        "calculated_at",
    ]
    list_filter = [
        "is_self_practice_eligible",
        "is_osce_eligible",
        "module_offering__academic_year",
        "module_offering__semester",
    ]
    search_fields = [
        "student__username",
        "student__student_profile__registration_number",
        "module_offering__module__code",
        "module_offering__module__title",
    ]


@admin.register(AttendanceChangeLog)
class AttendanceChangeLogAdmin(admin.ModelAdmin):
    list_display = [
        "attendance_record",
        "actor",
        "old_status",
        "new_status",
        "created_at",
    ]
    list_filter = [
        "old_status",
        "new_status",
        "created_at",
    ]
    search_fields = [
        "attendance_record__student__username",
        "actor__username",
        "change_reason",
    ]
    readonly_fields = [
        "attendance_record",
        "actor",
        "old_status",
        "new_status",
        "old_remarks",
        "new_remarks",
        "change_reason",
        "created_at",
    ]

    def has_add_permission(self, request):
        return False
    

@admin.register(SelfPracticeAttendanceRecord)
class SelfPracticeAttendanceRecordAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "self_practice_session",
        "status",
        "recorded_by",
        "recorded_at",
    ]
    list_filter = [
        "status",
        "recorded_at",
    ]
    search_fields = [
        "student__username",
        "student__student_profile__registration_number",
        "self_practice_session__module_offering__module__code",
    ]