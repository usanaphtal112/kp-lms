from django import forms

from .models import AttendanceRecord, AttendanceStatus


class BootstrapFormMixin:
    def apply_bootstrap_classes(self):
        for field in self.fields.values():
            widget = field.widget

            if isinstance(widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(widget, forms.Select):
                css_class = "form-select"
            elif isinstance(widget, forms.Textarea):
                css_class = "form-control"
                widget.attrs.setdefault("rows", 3)
            else:
                css_class = "form-control"

            existing_classes = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing_classes} {css_class}".strip()


class AttendanceSessionFilterForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search topic, module code, lecturer, cohort...",
            }
        ),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[
            ("", "All statuses"),
            ("SCHEDULED", "Scheduled"),
            ("COMPLETED", "Completed"),
            ("CANCELLED", "Cancelled"),
        ],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class AttendanceRecordUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = [
            "status",
            "remarks",
        ]

    change_reason = forms.CharField(
        required=False,
        widget=forms.Textarea,
        help_text="Recommended when changing an already recorded attendance status.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["status"].choices = AttendanceStatus.choices
        self.apply_bootstrap_classes()