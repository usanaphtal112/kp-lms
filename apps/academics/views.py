from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from .forms import (
    AcademicYearForm,
    CohortForm,
    CreditTransferForm,
    DepartmentForm,
    FacultyForm,
    ModuleEnrollmentForm,
    ModuleForm,
    ModuleOfferingForm,
    ProcedureForm,
    ProcedureRequirementForm,
    ProgramForm,
    SemesterForm,
)
from .mixins import AcademicManagerRequiredMixin
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
from .services import (
    approve_credit_transfer,
    create_missing_procedure_requirements,
    enroll_cohort_students,
    reject_credit_transfer,
    set_current_academic_year,
    set_current_semester,
)


def resolve_attr(obj, attr_path):
    value = obj

    for part in attr_path.split("__"):
        value = getattr(value, part)

    if callable(value):
        value = value()

    return value


class AcademicDashboardView(AcademicManagerRequiredMixin, TemplateView):
    template_name = "academics/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["counts"] = {
            "faculties": Faculty.objects.count(),
            "departments": Department.objects.count(),
            "programs": Program.objects.count(),
            "cohorts": Cohort.objects.count(),
            "modules": Module.objects.count(),
            "offerings": ModuleOffering.objects.count(),
            "enrollments": ModuleEnrollment.objects.count(),
            "credit_transfers": CreditTransfer.objects.count(),
        }

        context["current_academic_year"] = AcademicYear.objects.filter(
            is_current=True
        ).first()
        context["current_semester"] = Semester.objects.filter(
            is_current=True
        ).first()

        return context


class AcademicListView(AcademicManagerRequiredMixin, ListView):
    template_name = "academics/object_list.html"
    paginate_by = 20
    table_columns = []
    create_url_name = None
    update_url_name = None
    detail_url_name = None
    page_title = ""
    page_subtitle = ""

    def get_table_rows(self):
        rows = []

        for obj in self.object_list:
            rows.append(
                {
                    "object": obj,
                    "cells": [
                        resolve_attr(obj, attr_path)
                        for _, attr_path in self.table_columns
                    ],
                }
            )

        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["page_subtitle"] = self.page_subtitle
        context["table_headers"] = [label for label, _ in self.table_columns]
        context["table_rows"] = self.get_table_rows()
        context["create_url_name"] = self.create_url_name
        context["update_url_name"] = self.update_url_name
        context["detail_url_name"] = self.detail_url_name

        return context


class AcademicCreateView(AcademicManagerRequiredMixin, CreateView):
    template_name = "academics/object_form.html"
    page_title = ""
    submit_label = "Create"
    success_url_name = None

    def get_success_url(self):
        return reverse_lazy(self.success_url_name)

    def form_valid(self, form):
        messages.success(self.request, f"{self.model.__name__} created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["submit_label"] = self.submit_label
        return context


class AcademicUpdateView(AcademicManagerRequiredMixin, UpdateView):
    template_name = "academics/object_form.html"
    page_title = ""
    submit_label = "Save changes"
    success_url_name = None

    def get_success_url(self):
        return reverse_lazy(self.success_url_name)

    def form_valid(self, form):
        messages.success(self.request, f"{self.model.__name__} updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["submit_label"] = self.submit_label
        return context
    
class FacultyListView(AcademicListView):
    model = Faculty
    page_title = "Faculties"
    page_subtitle = "Manage institution faculties."
    table_columns = [
        ("Code", "code"),
        ("Name", "name"),
        ("Active", "is_active"),
    ]
    create_url_name = "academics:faculty_create"
    update_url_name = "academics:faculty_update"


class FacultyCreateView(AcademicCreateView):
    model = Faculty
    form_class = FacultyForm
    page_title = "Create faculty"
    success_url_name = "academics:faculty_list"


class FacultyUpdateView(AcademicUpdateView):
    model = Faculty
    form_class = FacultyForm
    page_title = "Update faculty"
    success_url_name = "academics:faculty_list"


class DepartmentListView(AcademicListView):
    model = Department
    page_title = "Departments"
    page_subtitle = "Manage departments under faculties."
    table_columns = [
        ("Code", "code"),
        ("Name", "name"),
        ("Faculty", "faculty"),
        ("Active", "is_active"),
    ]
    create_url_name = "academics:department_create"
    update_url_name = "academics:department_update"

    def get_queryset(self):
        return Department.objects.select_related("faculty")


class DepartmentCreateView(AcademicCreateView):
    model = Department
    form_class = DepartmentForm
    page_title = "Create department"
    success_url_name = "academics:department_list"


class DepartmentUpdateView(AcademicUpdateView):
    model = Department
    form_class = DepartmentForm
    page_title = "Update department"
    success_url_name = "academics:department_list"


class ProgramListView(AcademicListView):
    model = Program
    page_title = "Programs"
    page_subtitle = "Manage academic programs."
    table_columns = [
        ("Code", "code"),
        ("Name", "name"),
        ("Department", "department"),
        ("Award", "get_award_type_display"),
        ("Duration", "duration_years"),
    ]
    create_url_name = "academics:program_create"
    update_url_name = "academics:program_update"

    def get_queryset(self):
        return Program.objects.select_related("department", "department__faculty")


class ProgramCreateView(AcademicCreateView):
    model = Program
    form_class = ProgramForm
    page_title = "Create program"
    success_url_name = "academics:program_list"


class ProgramUpdateView(AcademicUpdateView):
    model = Program
    form_class = ProgramForm
    page_title = "Update program"
    success_url_name = "academics:program_list"


class CohortListView(AcademicListView):
    model = Cohort
    page_title = "Cohorts"
    page_subtitle = "Manage student cohorts."
    table_columns = [
        ("Code", "code"),
        ("Name", "name"),
        ("Program", "program"),
        ("Intake", "intake_year"),
        ("Status", "get_status_display"),
    ]
    create_url_name = "academics:cohort_create"
    update_url_name = "academics:cohort_update"

    def get_queryset(self):
        return Cohort.objects.select_related("program", "program__department")


class CohortCreateView(AcademicCreateView):
    model = Cohort
    form_class = CohortForm
    page_title = "Create cohort"
    success_url_name = "academics:cohort_list"


class CohortUpdateView(AcademicUpdateView):
    model = Cohort
    form_class = CohortForm
    page_title = "Update cohort"
    success_url_name = "academics:cohort_list"


class AcademicYearListView(AcademicListView):
    model = AcademicYear
    page_title = "Academic years"
    page_subtitle = "Manage academic years and current year."
    table_columns = [
        ("Name", "name"),
        ("Start", "start_date"),
        ("End", "end_date"),
        ("Current", "is_current"),
    ]
    create_url_name = "academics:academic_year_create"
    update_url_name = "academics:academic_year_update"


class AcademicYearCreateView(AcademicCreateView):
    model = AcademicYear
    form_class = AcademicYearForm
    page_title = "Create academic year"
    success_url_name = "academics:academic_year_list"


class AcademicYearUpdateView(AcademicUpdateView):
    model = AcademicYear
    form_class = AcademicYearForm
    page_title = "Update academic year"
    success_url_name = "academics:academic_year_list"


class SetCurrentAcademicYearView(AcademicManagerRequiredMixin, View):
    def post(self, request, pk):
        academic_year = get_object_or_404(AcademicYear, pk=pk)
        set_current_academic_year(academic_year)

        messages.success(request, f"{academic_year.name} is now the current academic year.")

        return redirect("academics:academic_year_list")


class SemesterListView(AcademicListView):
    model = Semester
    page_title = "Semesters"
    page_subtitle = "Manage semesters and current semester."
    table_columns = [
        ("Name", "name"),
        ("Academic Year", "academic_year"),
        ("Number", "get_semester_number_display"),
        ("Start", "start_date"),
        ("End", "end_date"),
        ("Current", "is_current"),
    ]
    create_url_name = "academics:semester_create"
    update_url_name = "academics:semester_update"

    def get_queryset(self):
        return Semester.objects.select_related("academic_year")


class SemesterCreateView(AcademicCreateView):
    model = Semester
    form_class = SemesterForm
    page_title = "Create semester"
    success_url_name = "academics:semester_list"


class SemesterUpdateView(AcademicUpdateView):
    model = Semester
    form_class = SemesterForm
    page_title = "Update semester"
    success_url_name = "academics:semester_list"


class SetCurrentSemesterView(AcademicManagerRequiredMixin, View):
    def post(self, request, pk):
        semester = get_object_or_404(Semester, pk=pk)
        set_current_semester(semester)

        messages.success(request, f"{semester.name} is now the current semester.")

        return redirect("academics:semester_list")


class ModuleListView(AcademicListView):
    model = Module
    page_title = "Modules"
    page_subtitle = "Manage module-based competency structure."
    table_columns = [
        ("Code", "code"),
        ("Title", "title"),
        ("Program", "program"),
        ("Year", "get_year_level_display"),
        ("Semester", "get_semester_number_display"),
        ("Attendance %", "attendance_requirement"),
        ("Pass %", "pass_mark"),
    ]
    create_url_name = "academics:module_create"
    update_url_name = "academics:module_update"
    detail_url_name = "academics:module_detail"

    def get_queryset(self):
        return Module.objects.select_related("program", "program__department")


class ModuleCreateView(AcademicCreateView):
    model = Module
    form_class = ModuleForm
    page_title = "Create module"
    success_url_name = "academics:module_list"


class ModuleUpdateView(AcademicUpdateView):
    model = Module
    form_class = ModuleForm
    page_title = "Update module"
    success_url_name = "academics:module_list"


class ModuleDetailView(AcademicManagerRequiredMixin, DetailView):
    model = Module
    template_name = "academics/module_detail.html"
    context_object_name = "module"

    def get_queryset(self):
        return Module.objects.select_related("program").prefetch_related(
            "procedures",
            "prerequisites",
        )
    
class ModuleOfferingListView(AcademicListView):
    model = ModuleOffering
    page_title = "Module offerings"
    page_subtitle = "Manage modules offered to cohorts in a semester."
    table_columns = [
        ("Module", "module"),
        ("Cohort", "cohort"),
        ("Academic Year", "academic_year"),
        ("Semester", "semester"),
        ("Coordinator", "coordinator"),
        ("Status", "get_status_display"),
    ]
    create_url_name = "academics:offering_create"
    update_url_name = "academics:offering_update"
    detail_url_name = "academics:offering_detail"

    def get_queryset(self):
        return ModuleOffering.objects.select_related(
            "module",
            "cohort",
            "academic_year",
            "semester",
            "coordinator",
        )


class ModuleOfferingCreateView(AcademicCreateView):
    model = ModuleOffering
    form_class = ModuleOfferingForm
    page_title = "Create module offering"
    success_url_name = "academics:offering_list"

    def form_valid(self, form):
        response = super().form_valid(form)
        create_missing_procedure_requirements(self.object)
        return response


class ModuleOfferingUpdateView(AcademicUpdateView):
    model = ModuleOffering
    form_class = ModuleOfferingForm
    page_title = "Update module offering"
    success_url_name = "academics:offering_list"


class ModuleOfferingDetailView(AcademicManagerRequiredMixin, DetailView):
    model = ModuleOffering
    template_name = "academics/offering_detail.html"
    context_object_name = "offering"

    def get_queryset(self):
        return ModuleOffering.objects.select_related(
            "module",
            "cohort",
            "academic_year",
            "semester",
            "coordinator",
        ).prefetch_related(
            "enrollments__student",
            "procedure_requirements__procedure",
        )


class EnrollCohortStudentsView(AcademicManagerRequiredMixin, View):
    def post(self, request, pk):
        offering = get_object_or_404(ModuleOffering, pk=pk)
        result = enroll_cohort_students(offering)

        messages.success(
            request,
            (
                f"Cohort enrollment completed. "
                f"Created: {result['created_count']}, "
                f"Existing: {result['existing_count']}."
            ),
        )

        return redirect("academics:offering_detail", pk=offering.pk)


class ProcedureListView(AcademicListView):
    model = Procedure
    page_title = "Procedures"
    page_subtitle = "Manage clinical skills procedures under modules."
    table_columns = [
        ("Code", "code"),
        ("Name", "name"),
        ("Module", "module"),
        ("Required practice", "minimum_required_practices"),
        ("Required", "is_required"),
    ]
    create_url_name = "academics:procedure_create"
    update_url_name = "academics:procedure_update"

    def get_queryset(self):
        return Procedure.objects.select_related("module", "module__program")


class ProcedureCreateView(AcademicCreateView):
    model = Procedure
    form_class = ProcedureForm
    page_title = "Create procedure"
    success_url_name = "academics:procedure_list"


class ProcedureUpdateView(AcademicUpdateView):
    model = Procedure
    form_class = ProcedureForm
    page_title = "Update procedure"
    success_url_name = "academics:procedure_list"


class ProcedureRequirementListView(AcademicListView):
    model = ProcedureRequirement
    page_title = "Procedure requirements"
    page_subtitle = "Manage required procedures for module offerings."
    table_columns = [
        ("Offering", "module_offering"),
        ("Procedure", "procedure"),
        ("Required count", "required_count"),
        ("Due date", "due_date"),
        ("Mandatory", "is_mandatory"),
    ]
    create_url_name = "academics:procedure_requirement_create"
    update_url_name = "academics:procedure_requirement_update"

    def get_queryset(self):
        return ProcedureRequirement.objects.select_related(
            "module_offering",
            "module_offering__module",
            "procedure",
        )


class ProcedureRequirementCreateView(AcademicCreateView):
    model = ProcedureRequirement
    form_class = ProcedureRequirementForm
    page_title = "Create procedure requirement"
    success_url_name = "academics:procedure_requirement_list"


class ProcedureRequirementUpdateView(AcademicUpdateView):
    model = ProcedureRequirement
    form_class = ProcedureRequirementForm
    page_title = "Update procedure requirement"
    success_url_name = "academics:procedure_requirement_list"


class ModuleEnrollmentListView(AcademicListView):
    model = ModuleEnrollment
    page_title = "Module enrollments"
    page_subtitle = "Manage student enrollment into module offerings."
    table_columns = [
        ("Student", "student"),
        ("Module offering", "module_offering"),
        ("Type", "get_enrollment_type_display"),
        ("Status", "get_status_display"),
        ("Enrolled on", "enrolled_on"),
    ]
    create_url_name = "academics:enrollment_create"
    update_url_name = "academics:enrollment_update"

    def get_queryset(self):
        return ModuleEnrollment.objects.select_related(
            "student",
            "student__student_profile",
            "module_offering",
            "module_offering__module",
            "module_offering__cohort",
        )


class ModuleEnrollmentCreateView(AcademicCreateView):
    model = ModuleEnrollment
    form_class = ModuleEnrollmentForm
    page_title = "Create module enrollment"
    success_url_name = "academics:enrollment_list"


class ModuleEnrollmentUpdateView(AcademicUpdateView):
    model = ModuleEnrollment
    form_class = ModuleEnrollmentForm
    page_title = "Update module enrollment"
    success_url_name = "academics:enrollment_list"


class CreditTransferListView(AcademicListView):
    model = CreditTransfer
    page_title = "Credit transfers"
    page_subtitle = "Manage credit transfer module exemptions."
    table_columns = [
        ("Student", "student"),
        ("Module", "module"),
        ("Previous institution", "previous_institution"),
        ("Previous mark", "previous_mark"),
        ("Status", "get_status_display"),
    ]
    create_url_name = "academics:credit_transfer_create"
    update_url_name = "academics:credit_transfer_update"

    def get_queryset(self):
        return CreditTransfer.objects.select_related(
            "student",
            "module",
            "approved_by",
        )


class CreditTransferCreateView(AcademicCreateView):
    model = CreditTransfer
    form_class = CreditTransferForm
    page_title = "Create credit transfer"
    success_url_name = "academics:credit_transfer_list"


class CreditTransferUpdateView(AcademicUpdateView):
    model = CreditTransfer
    form_class = CreditTransferForm
    page_title = "Update credit transfer"
    success_url_name = "academics:credit_transfer_list"


class ApproveCreditTransferView(AcademicManagerRequiredMixin, View):
    def post(self, request, pk):
        credit_transfer = get_object_or_404(CreditTransfer, pk=pk)
        approve_credit_transfer(
            credit_transfer=credit_transfer,
            approved_by=request.user,
        )

        messages.success(request, "Credit transfer approved.")

        return redirect("academics:credit_transfer_list")


class RejectCreditTransferView(AcademicManagerRequiredMixin, View):
    def post(self, request, pk):
        credit_transfer = get_object_or_404(CreditTransfer, pk=pk)
        reject_credit_transfer(
            credit_transfer=credit_transfer,
            approved_by=request.user,
        )

        messages.success(request, "Credit transfer rejected.")

        return redirect("academics:credit_transfer_list")