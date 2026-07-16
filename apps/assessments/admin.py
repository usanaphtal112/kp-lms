from django.contrib import admin

from .models import (
    OSCEAttempt,
    OSCEExam,
    OSCEResult,
    OSCERubricItem,
    OSCEScore,
    OSCEStation,
    RetakeRequest,
    OSCEMarkAuditLog,
)


class OSCEStationInline(admin.TabularInline):
    model = OSCEStation
    extra = 1


@admin.register(OSCEExam)
class OSCEExamAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "module_offering",
        "exam_date",
        "status",
        "created_by",
        "approved_by",
        "published_at",
    ]
    list_filter = [
        "status",
        "exam_date",
        "module_offering__academic_year",
        "module_offering__semester",
    ]
    search_fields = [
        "title",
        "module_offering__module__code",
        "module_offering__module__title",
        "module_offering__cohort__code",
    ]
    autocomplete_fields = [
        "module_offering",
        "created_by",
        "approved_by",
        "published_by",
    ]
    inlines = [OSCEStationInline]


class OSCERubricItemInline(admin.TabularInline):
    model = OSCERubricItem
    extra = 3


@admin.register(OSCEStation)
class OSCEStationAdmin(admin.ModelAdmin):
    list_display = [
        "osce_exam",
        "station_order",
        "title",
        "procedure",
        "max_score",
        "duration_minutes",
        "is_active",
    ]
    list_filter = [
        "is_active",
        "osce_exam__status",
    ]
    search_fields = [
        "title",
        "procedure__code",
        "procedure__name",
        "osce_exam__title",
    ]
    autocomplete_fields = [
        "osce_exam",
        "procedure",
    ]
    inlines = [OSCERubricItemInline]


@admin.register(OSCERubricItem)
class OSCERubricItemAdmin(admin.ModelAdmin):
    list_display = [
        "station",
        "item_order",
        "criterion",
        "max_score",
        "is_critical",
    ]
    list_filter = [
        "is_critical",
        "station__osce_exam",
    ]
    search_fields = [
        "criterion",
        "station__title",
        "station__osce_exam__title",
    ]


@admin.register(OSCEAttempt)
class OSCEAttemptAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "osce_exam",
        "attempt_number",
        "attempt_type",
        "status",
        "submitted_at",
    ]
    list_filter = [
        "attempt_type",
        "status",
        "osce_exam__module_offering__academic_year",
    ]
    search_fields = [
        "student__username",
        "student__student_profile__registration_number",
        "osce_exam__title",
    ]
    autocomplete_fields = [
        "osce_exam",
        "student",
        "created_by",
        "submitted_by",
    ]


@admin.register(OSCEScore)
class OSCEScoreAdmin(admin.ModelAdmin):
    list_display = [
        "attempt",
        "station",
        "rubric_item",
        "score",
        "marked_by",
        "marked_at",
    ]
    list_filter = [
        "station__osce_exam",
        "marked_at",
    ]
    search_fields = [
        "attempt__student__username",
        "attempt__student__student_profile__registration_number",
        "rubric_item__criterion",
    ]
    autocomplete_fields = [
        "attempt",
        "station",
        "rubric_item",
        "marked_by",
    ]


@admin.register(OSCEResult)
class OSCEResultAdmin(admin.ModelAdmin):
    list_display = [
        "attempt",
        "percentage",
        "final_mark",
        "pass_mark",
        "is_passed",
        "approved_by",
        "is_published",
    ]
    list_filter = [
        "is_passed",
        "is_published",
        "attempt__attempt_type",
    ]
    search_fields = [
        "attempt__student__username",
        "attempt__student__student_profile__registration_number",
        "attempt__osce_exam__title",
    ]
    autocomplete_fields = [
        "attempt",
        "approved_by",
    ]


@admin.register(RetakeRequest)
class RetakeRequestAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "osce_exam",
        "original_attempt",
        "status",
        "reviewed_by",
        "created_at",
    ]
    list_filter = [
        "status",
        "created_at",
    ]
    search_fields = [
        "student__username",
        "student__student_profile__registration_number",
        "osce_exam__title",
    ]
    autocomplete_fields = [
        "student",
        "osce_exam",
        "original_attempt",
        "reviewed_by",
        "created_attempt",
    ]

@admin.register(OSCEMarkAuditLog)
class OSCEMarkAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "attempt",
        "rubric_item",
        "actor",
        "old_score",
        "new_score",
        "created_at",
    ]
    search_fields = [
        "attempt__student__username",
        "attempt__student__student_profile__registration_number",
        "rubric_item__criterion",
        "reason",
    ]
    list_filter = ["created_at"]
    readonly_fields = [
        "score",
        "attempt",
        "rubric_item",
        "actor",
        "old_score",
        "new_score",
        "reason",
        "created_at",
    ]

    def has_add_permission(self, request):
        return False