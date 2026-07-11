from django.contrib import admin

from .models import (
    DemonstrationProcedure,
    DemonstrationSession,
    LabRoom,
    ProcedureLog,
    SelfPracticeProcedure,
    SelfPracticeSession,
)


@admin.register(DemonstrationSession)
class DemonstrationSessionAdmin(admin.ModelAdmin):
    list_display = ["topic", "module_offering", "lecturer", "status", "booking"]
    list_filter = ["status", "module_offering__academic_year", "module_offering__semester"]

    search_fields = [
        "topic", 
        "description", 
        "module_offering__module__title", 
        "module_offering__module__code"
    ]


@admin.register(DemonstrationProcedure)
class DemonstrationProcedureAdmin(admin.ModelAdmin):
    list_display = ["demonstration_session", "procedure"]
    search_fields = [
        "demonstration_session__topic", 
        "procedure__title", 
        "procedure__code"
    ]

@admin.register(LabRoom)
class LabRoomAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "location", "capacity", "is_active"]
    search_fields = ["code", "name", "location"]
    list_filter = ["is_active"]


class SelfPracticeProcedureInline(admin.TabularInline):
    model = SelfPracticeProcedure
    extra = 1


class ProcedureLogInline(admin.TabularInline):
    model = ProcedureLog
    extra = 0
    readonly_fields = ["verified_at"]


@admin.register(SelfPracticeSession)
class SelfPracticeSessionAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "module_offering",
        "supervisor",
        "status",
        "booking",
    ]
    search_fields = [
        "student__username",
        "student__student_profile__registration_number",
        "module_offering__module__code",
    ]
    list_filter = [
        "status",
        "module_offering__academic_year",
        "module_offering__semester",
    ]
    autocomplete_fields = [
        "student",
        "supervisor",
        "module_offering",
        "booking",
    ]
    inlines = [
        SelfPracticeProcedureInline,
        ProcedureLogInline,
    ]


@admin.register(SelfPracticeProcedure)
class SelfPracticeProcedureAdmin(admin.ModelAdmin):
    list_display = [
        "self_practice_session",
        "procedure",
    ]
    search_fields = [
        "self_practice_session__student__username",
        "procedure__code",
        "procedure__name",
    ]


@admin.register(ProcedureLog)
class ProcedureLogAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "procedure",
        "module_offering",
        "performed_count",
        "status",
        "verified_by",
        "verified_at",
    ]
    list_filter = [
        "status",
        "module_offering__academic_year",
        "module_offering__semester",
    ]
    search_fields = [
        "student__username",
        "student__student_profile__registration_number",
        "procedure__code",
        "procedure__name",
    ]
    autocomplete_fields = [
        "student",
        "module_offering",
        "procedure",
        "verified_by",
    ]