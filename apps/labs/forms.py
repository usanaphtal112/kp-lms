from django import forms

from django.contrib.auth import get_user_model

from apps.academics.models import ModuleOffering, Procedure
from apps.accounts.models import UserRole
from apps.attendance.models import AttendanceStatus

from .models import LabRoom

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


class SelfPracticeBookingForm(BootstrapFormMixin, forms.Form):
    module_offering = forms.ModelChoiceField(
        queryset=ModuleOffering.objects.none(),
    )
    lab_room = forms.ModelChoiceField(
        queryset=LabRoom.objects.filter(is_active=True),
    )
    start_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    end_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    procedures = forms.ModelMultipleChoiceField(
        queryset=Procedure.objects.none(),
        required=False,
        help_text="Select the procedures you plan to practice.",
    )
    objectives = forms.CharField(
        required=False,
        widget=forms.Textarea,
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea,
    )

    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop("student")
        super().__init__(*args, **kwargs)

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

        module_offering_id = None

        if self.data.get("module_offering"):
            module_offering_id = self.data.get("module_offering")
        elif self.initial.get("module_offering"):
            module_offering_id = self.initial.get("module_offering")

        if module_offering_id:
            module_offering = ModuleOffering.objects.filter(
                pk=module_offering_id
            ).first()

            if module_offering:
                self.fields["procedures"].queryset = Procedure.objects.filter(
                    module=module_offering.module,
                    is_active=True,
                )

        self.apply_bootstrap_classes()

    def clean(self):
        cleaned_data = super().clean()

        start_at = cleaned_data.get("start_at")
        end_at = cleaned_data.get("end_at")

        if start_at and end_at and start_at >= end_at:
            raise forms.ValidationError("End time must be after start time.")

        return cleaned_data


class SelfPracticeApprovalForm(BootstrapFormMixin, forms.Form):
    supervisor = forms.ModelChoiceField(
        queryset=get_user_model().objects.none(),
        required=False,
        help_text="Optional. Assign a lecturer, lab coordinator, or administration user to supervise.",
    )
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        User = get_user_model()
        self.fields["supervisor"].queryset = User.objects.filter(
            role__in=[
                UserRole.LECTURER,
                UserRole.LAB_COORDINATOR,
                UserRole.ADMINISTRATION,
                UserRole.IT_ADMIN,
            ],
            is_active=True,
        ).order_by("first_name", "last_name", "username")

        self.apply_bootstrap_classes()


class SelfPracticeRejectForm(BootstrapFormMixin, forms.Form):
    reason = forms.CharField(widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class SelfPracticeOutcomeForm(BootstrapFormMixin, forms.Form):
    attendance_status = forms.ChoiceField(
        choices=AttendanceStatus.choices,
        initial=AttendanceStatus.PRESENT,
    )
    performed_procedures = forms.ModelMultipleChoiceField(
        queryset=Procedure.objects.none(),
        required=False,
        help_text="Select procedures actually performed and verified during this session.",
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea,
    )

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop("session")
        super().__init__(*args, **kwargs)

        self.fields["performed_procedures"].queryset = Procedure.objects.filter(
            module=self.session.module_offering.module,
            is_active=True,
        )

        self.apply_bootstrap_classes()


class LabRoomForm(forms.ModelForm):
    class Meta:
        model = LabRoom
        fields = [
            "name",
            "code",
            "location",
            "capacity",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"