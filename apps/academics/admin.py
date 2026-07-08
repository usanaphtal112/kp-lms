from django.contrib import admin

from .models import (
    AcademicYear,
    Cohort,
    CreditTransfer,
    Department,
    Faculty,
    Module,
    ModuleEnrollment,
    ModuleOffering,
    Procedure,
    ProcedureRequirement,
    Program,
    Semester,
)


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "is_active"]
    search_fields = ["name", "code"]
    list_filter = ["is_active"]


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "faculty", "is_active"]
    search_fields = ["name", "code", "faculty__name"]
    list_filter = ["faculty", "is_active"]


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "department", "award_type", "duration_years", "is_active"]
    search_fields = ["name", "code", "department__name"]
    list_filter = ["award_type", "department", "is_active"]


@admin.register(Cohort)
class CohortAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "program", "intake_year", "graduation_year", "status", "is_active"]
    search_fields = ["name", "code", "program__name"]
    list_filter = ["program", "status", "intake_year", "is_active"]


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ["name", "start_date", "end_date", "is_current", "is_active"]
    list_filter = ["is_current", "is_active"]


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ["name", "academic_year", "semester_number", "start_date", "end_date", "is_current"]
    list_filter = ["academic_year", "semester_number", "is_current"]


class ProcedureInline(admin.TabularInline):
    model = Procedure
    extra = 1


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "title",
        "program",
        "year_level",
        "semester_number",
        "attendance_requirement",
        "pass_mark",
        "is_active",
    ]
    search_fields = ["code", "title", "program__name"]
    list_filter = ["program", "year_level", "semester_number", "is_active"]
    filter_horizontal = ["prerequisites"]
    inlines = [ProcedureInline]


@admin.register(ModuleOffering)
class ModuleOfferingAdmin(admin.ModelAdmin):
    list_display = ["module", "cohort", "academic_year", "semester", "coordinator", "status", "is_active"]
    search_fields = ["module__code", "module__title", "cohort__code"]
    list_filter = ["academic_year", "semester", "status", "is_active"]
    autocomplete_fields = ["module", "cohort", "coordinator"]


@admin.register(Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "module", "minimum_required_practices", "is_required", "is_active"]
    search_fields = ["code", "name", "module__code", "module__title"]
    list_filter = ["module", "is_required", "is_active"]


@admin.register(ProcedureRequirement)
class ProcedureRequirementAdmin(admin.ModelAdmin):
    list_display = ["module_offering", "procedure", "required_count", "due_date", "is_mandatory"]
    search_fields = ["module_offering__module__code", "procedure__name"]
    list_filter = ["is_mandatory", "is_active"]


@admin.register(ModuleEnrollment)
class ModuleEnrollmentAdmin(admin.ModelAdmin):
    list_display = ["student", "module_offering", "enrollment_type", "status", "enrolled_on"]
    search_fields = [
        "student__username",
        "student__first_name",
        "student__last_name",
        "student__student_profile__registration_number",
        "module_offering__module__code",
    ]
    list_filter = ["enrollment_type", "status", "module_offering__academic_year"]


@admin.register(CreditTransfer)
class CreditTransferAdmin(admin.ModelAdmin):
    list_display = ["student", "module", "previous_institution", "previous_mark", "status", "approved_by"]
    search_fields = ["student__username", "module__code", "previous_institution", "previous_module_name"]
    list_filter = ["status", "module__program"]