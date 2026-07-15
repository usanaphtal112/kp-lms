from pathlib import Path

from django import forms
from django.conf import settings

from apps.academics.models import ModuleOffering
from apps.accounts.models import UserRole

from .models import (
    ClinicalReport,
    ClinicalTeachingReport,
    PortfolioItem,
    ReportReviewDecision,
)


class BootstrapFormMixin:
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


def validate_report_attachment(uploaded_file):
    if not uploaded_file:
        return uploaded_file

    max_size = settings.KPLMS_MAX_REPORT_UPLOAD_SIZE_MB * 1024 * 1024

    if uploaded_file.size > max_size:
        raise forms.ValidationError(
            f"File is too large. Maximum allowed size is "
            f"{settings.KPLMS_MAX_REPORT_UPLOAD_SIZE_MB} MB."
        )

    extension = Path(uploaded_file.name).suffix.lower().replace(".", "")

    if extension not in settings.KPLMS_ALLOWED_REPORT_EXTENSIONS:
        raise forms.ValidationError(
            "Unsupported file type for report attachment."
        )

    return uploaded_file


class ClinicalReportForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ClinicalReport
        fields = [
            "module_offering",
            "title",
            "facility_name",
            "department_or_unit",
            "clinical_start_date",
            "clinical_end_date",
            "activities_performed",
            "skills_practiced",
            "reflection",
            "challenges",
            "supervisor_name",
            "attachment",
        ]
        widgets = {
            "clinical_start_date": forms.DateInput(attrs={"type": "date"}),
            "clinical_end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop("student", None)
        super().__init__(*args, **kwargs)

        if self.student:
            self.fields["module_offering"].queryset = ModuleOffering.objects.filter(
                enrollments__student=self.student,
                enrollments__is_active=True,
                is_active=True,
            ).select_related(
                "module",
                "cohort",
                "academic_year",
                "semester",
            ).distinct()

        self.apply_bootstrap_classes()

    def clean_attachment(self):
        return validate_report_attachment(self.cleaned_data.get("attachment"))


class ClinicalTeachingReportForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ClinicalTeachingReport
        fields = [
            "module_offering",
            "title",
            "facility_name",
            "department_or_unit",
            "teaching_date",
            "topic_taught",
            "students_supervised_count",
            "objectives",
            "teaching_activities",
            "observations",
            "recommendations",
            "attachment",
        ]
        widgets = {
            "teaching_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        self.lecturer = kwargs.pop("lecturer", None)
        super().__init__(*args, **kwargs)

        queryset = ModuleOffering.objects.select_related(
            "module",
            "cohort",
            "academic_year",
            "semester",
        ).filter(is_active=True)

        if self.lecturer and getattr(self.lecturer, "role", None) == UserRole.LECTURER:
            queryset = queryset.filter(coordinator=self.lecturer)

        self.fields["module_offering"].queryset = queryset
        self.apply_bootstrap_classes()

    def clean_attachment(self):
        return validate_report_attachment(self.cleaned_data.get("attachment"))


class ReportReviewForm(BootstrapFormMixin, forms.Form):
    decision = forms.ChoiceField(
        choices=ReportReviewDecision.choices,
    )
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class PortfolioItemForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = PortfolioItem
        fields = [
            "module_offering",
            "item_type",
            "title",
            "description",
            "evidence_file",
            "is_visible_to_student",
        ]

    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop("student", None)
        super().__init__(*args, **kwargs)

        if self.student:
            self.fields["module_offering"].queryset = ModuleOffering.objects.filter(
                enrollments__student=self.student,
                enrollments__is_active=True,
            ).distinct()

        self.apply_bootstrap_classes()

    def clean_evidence_file(self):
        return validate_report_attachment(self.cleaned_data.get("evidence_file"))