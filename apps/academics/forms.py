from django import forms
from django.contrib.auth import get_user_model

from apps.accounts.models import UserRole

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


class BootstrapModelFormMixin:
    def apply_bootstrap_classes(self):
        for field in self.fields.values():
            widget = field.widget

            if isinstance(widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(widget, forms.Select):
                css_class = "form-select"
            elif isinstance(widget, forms.SelectMultiple):
                css_class = "form-select"
            elif isinstance(widget, forms.Textarea):
                css_class = "form-control"
                widget.attrs.setdefault("rows", 4)
            else:
                css_class = "form-control"

            existing_classes = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing_classes} {css_class}".strip()


class FacultyForm(BootstrapModelFormMixin, forms.ModelForm):
    class Meta:
        model = Faculty
        fields = ["name", "code", "description", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class DepartmentForm(BootstrapModelFormMixin, forms.ModelForm):
    class Meta:
        model = Department
        fields = ["faculty", "name", "code", "description", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class ProgramForm(BootstrapModelFormMixin, forms.ModelForm):
    class Meta:
        model = Program
        fields = [
            "department",
            "name",
            "code",
            "award_type",
            "duration_years",
            "description",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class CohortForm(BootstrapModelFormMixin, forms.ModelForm):
    class Meta:
        model = Cohort
        fields = [
            "program",
            "name",
            "code",
            "intake_year",
            "graduation_year",
            "status",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class AcademicYearForm(BootstrapModelFormMixin, forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ["name", "start_date", "end_date", "is_current", "is_active"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class SemesterForm(BootstrapModelFormMixin, forms.ModelForm):
    class Meta:
        model = Semester
        fields = [
            "academic_year",
            "name",
            "semester_number",
            "start_date",
            "end_date",
            "is_current",
            "is_active",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class ModuleForm(BootstrapModelFormMixin, forms.ModelForm):
    class Meta:
        model = Module
        fields = [
            "program",
            "code",
            "title",
            "year_level",
            "semester_number",
            "credits",
            "attendance_requirement",
            "pass_mark",
            "description",
            "prerequisites",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields["prerequisites"].queryset = Module.objects.exclude(
                pk=self.instance.pk
            )

        self.apply_bootstrap_classes()


class ModuleOfferingForm(BootstrapModelFormMixin, forms.ModelForm):
    class Meta:
        model = ModuleOffering
        fields = [
            "module",
            "cohort",
            "academic_year",
            "semester",
            "coordinator",
            "status",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        User = get_user_model()
        self.fields["coordinator"].queryset = User.objects.filter(
            role__in=[
                UserRole.LECTURER,
                UserRole.LAB_COORDINATOR,
                UserRole.ADMINISTRATION,
            ],
            is_active=True,
        ).order_by("first_name", "last_name", "username")

        self.apply_bootstrap_classes()


class ProcedureForm(BootstrapModelFormMixin, forms.ModelForm):
    class Meta:
        model = Procedure
        fields = [
            "module",
            "code",
            "name",
            "description",
            "minimum_required_practices",
            "is_required",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class ProcedureRequirementForm(BootstrapModelFormMixin, forms.ModelForm):
    class Meta:
        model = ProcedureRequirement
        fields = [
            "module_offering",
            "procedure",
            "required_count",
            "due_date",
            "is_mandatory",
            "is_active",
        ]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class ModuleEnrollmentForm(BootstrapModelFormMixin, forms.ModelForm):
    class Meta:
        model = ModuleEnrollment
        fields = [
            "student",
            "module_offering",
            "enrollment_type",
            "status",
            "enrolled_on",
            "completed_on",
            "remarks",
            "is_active",
        ]
        widgets = {
            "enrolled_on": forms.DateInput(attrs={"type": "date"}),
            "completed_on": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        User = get_user_model()
        self.fields["student"].queryset = User.objects.filter(
            role=UserRole.STUDENT,
            is_active=True,
        ).order_by("student_profile__registration_number", "first_name", "last_name")

        self.apply_bootstrap_classes()


class CreditTransferForm(BootstrapModelFormMixin, forms.ModelForm):
    class Meta:
        model = CreditTransfer
        fields = [
            "student",
            "module",
            "previous_institution",
            "previous_module_name",
            "previous_mark",
            "supporting_file",
            "status",
            "remarks",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        User = get_user_model()
        self.fields["student"].queryset = User.objects.filter(
            role=UserRole.STUDENT,
            is_active=True,
        ).order_by("student_profile__registration_number", "first_name", "last_name")

        self.apply_bootstrap_classes()