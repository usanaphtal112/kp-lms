from django.contrib import admin

from .models import (
    ClinicalReport,
    ClinicalTeachingReport,
    PortfolioItem,
    ReportReview,
)


@admin.register(ClinicalReport)
class ClinicalReportAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "student",
        "module_offering",
        "facility_name",
        "clinical_start_date",
        "status",
        "submitted_at",
        "reviewed_by",
    ]
    list_filter = [
        "status",
        "clinical_start_date",
        "module_offering__academic_year",
        "module_offering__semester",
    ]
    search_fields = [
        "title",
        "student__username",
        "student__student_profile__registration_number",
        "facility_name",
    ]
    autocomplete_fields = [
        "student",
        "module_offering",
        "reviewed_by",
    ]


@admin.register(ClinicalTeachingReport)
class ClinicalTeachingReportAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "lecturer",
        "module_offering",
        "facility_name",
        "teaching_date",
        "status",
        "submitted_at",
        "reviewed_by",
    ]
    list_filter = [
        "status",
        "teaching_date",
        "module_offering__academic_year",
        "module_offering__semester",
    ]
    search_fields = [
        "title",
        "lecturer__username",
        "facility_name",
        "topic_taught",
    ]
    autocomplete_fields = [
        "lecturer",
        "module_offering",
        "reviewed_by",
    ]


@admin.register(ReportReview)
class ReportReviewAdmin(admin.ModelAdmin):
    list_display = [
        "reviewer",
        "decision",
        "clinical_report",
        "clinical_teaching_report",
        "reviewed_at",
    ]
    list_filter = [
        "decision",
        "reviewed_at",
    ]
    search_fields = [
        "reviewer__username",
        "comments",
        "clinical_report__title",
        "clinical_teaching_report__title",
    ]
    autocomplete_fields = [
        "reviewer",
        "clinical_report",
        "clinical_teaching_report",
    ]


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "item_type",
        "title",
        "module_offering",
        "is_visible_to_student",
        "created_at",
    ]
    list_filter = [
        "item_type",
        "is_visible_to_student",
        "created_at",
    ]
    search_fields = [
        "student__username",
        "student__student_profile__registration_number",
        "title",
        "description",
    ]
    autocomplete_fields = [
        "student",
        "module_offering",
        "created_by",
    ]