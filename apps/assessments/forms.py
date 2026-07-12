from decimal import Decimal

from django import forms

from apps.academics.models import ModuleOffering, Procedure

from .models import (
    OSCEExam,
    OSCERubricItem,
    OSCEStation,
    RetakeRequest,
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


class OSCEExamForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = OSCEExam
        fields = [
            "module_offering",
            "title",
            "exam_date",
            "start_time",
            "end_time",
            "instructions",
            "status",
            "is_active",
        ]
        widgets = {
            "exam_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        queryset = ModuleOffering.objects.select_related(
            "module",
            "cohort",
            "academic_year",
            "semester",
        ).filter(is_active=True)

        if self.user and getattr(self.user, "role", None) == "LECTURER":
            queryset = queryset.filter(coordinator=self.user)

        self.fields["module_offering"].queryset = queryset
        self.apply_bootstrap_classes()


class OSCEStationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = OSCEStation
        fields = [
            "osce_exam",
            "procedure",
            "title",
            "station_order",
            "duration_minutes",
            "max_score",
            "instructions",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        self.osce_exam = kwargs.pop("osce_exam", None)
        super().__init__(*args, **kwargs)

        if self.osce_exam:
            self.fields["osce_exam"].initial = self.osce_exam
            self.fields["osce_exam"].disabled = True
            self.fields["procedure"].queryset = Procedure.objects.filter(
                module=self.osce_exam.module_offering.module,
                is_active=True,
            )

        self.apply_bootstrap_classes()


class OSCERubricItemForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = OSCERubricItem
        fields = [
            "station",
            "criterion",
            "max_score",
            "item_order",
            "is_critical",
        ]

    def __init__(self, *args, **kwargs):
        self.station = kwargs.pop("station", None)
        super().__init__(*args, **kwargs)

        if self.station:
            self.fields["station"].initial = self.station
            self.fields["station"].disabled = True

        self.apply_bootstrap_classes()


class OSCEMarkEntryForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.attempt = kwargs.pop("attempt")
        super().__init__(*args, **kwargs)

        rubric_items = OSCERubricItem.objects.select_related(
            "station"
        ).filter(
            station__osce_exam=self.attempt.osce_exam,
            station__is_active=True,
        ).order_by(
            "station__station_order",
            "item_order",
        )

        existing_scores = {
            score.rubric_item_id: score
            for score in self.attempt.scores.all()
        }

        for item in rubric_items:
            field_name = f"rubric_{item.pk}"
            existing_score = existing_scores.get(item.pk)

            self.fields[field_name] = forms.DecimalField(
                label=f"{item.station.station_order}. {item.criterion}",
                min_value=Decimal("0.00"),
                max_value=item.max_score,
                decimal_places=2,
                required=True,
                initial=existing_score.score if existing_score else Decimal("0.00"),
                help_text=f"Maximum: {item.max_score}",
                widget=forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "step": "0.01",
                    }
                ),
            )

    def get_score_data(self):
        score_data = {}

        rubric_items = OSCERubricItem.objects.select_related(
            "station"
        ).filter(
            station__osce_exam=self.attempt.osce_exam,
            station__is_active=True,
        )

        for item in rubric_items:
            score_data[item] = self.cleaned_data[f"rubric_{item.pk}"]

        return score_data


class RetakeRequestForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = RetakeRequest
        fields = [
            "reason",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class RetakeReviewForm(BootstrapFormMixin, forms.Form):
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()