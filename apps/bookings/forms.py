from django import forms

from apps.academics.models import ModuleOffering, Procedure
from apps.labs.models import LabRoom


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


class DemonstrationBookingForm(BootstrapFormMixin, forms.Form):
    module_offering = forms.ModelChoiceField(
        queryset=ModuleOffering.objects.none(),
    )
    lab_room = forms.ModelChoiceField(
        queryset=LabRoom.objects.filter(is_active=True),
    )
    title = forms.CharField(max_length=180)
    topic = forms.CharField(max_length=180)
    start_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    end_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    procedures = forms.ModelMultipleChoiceField(
        queryset=Procedure.objects.none(),
        required=False,
        help_text="Select procedures demonstrated in this session.",
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea,
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        module_offerings = ModuleOffering.objects.select_related(
            "module",
            "cohort",
            "academic_year",
            "semester",
        ).filter(is_active=True)

        if getattr(self.user, "role", None) == "LECTURER":
            module_offerings = module_offerings.filter(coordinator=self.user)

        self.fields["module_offering"].queryset = module_offerings

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


class BookingRejectForm(BootstrapFormMixin, forms.Form):
    reason = forms.CharField(widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()