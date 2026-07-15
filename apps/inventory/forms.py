from django import forms

from apps.assessments.models import OSCEExam
from apps.labs.models import DemonstrationSession, SelfPracticeSession

from .models import (
    InventoryCategory,
    InventoryUsage,
    InventoryUsageContext,
    InventoryUsageItem,
    StockBatch,
    StockItem,
    StockMovementType,
    Supplier,
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


class InventoryCategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = InventoryCategory
        fields = ["name", "code", "description", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class SupplierForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            "name",
            "contact_person",
            "phone_number",
            "email",
            "address",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class StockItemForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = StockItem
        fields = [
            "category",
            "name",
            "code",
            "item_type",
            "unit",
            "minimum_stock_level",
            "reorder_level",
            "description",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class StockBatchReceiveForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = StockBatch
        fields = [
            "stock_item",
            "supplier",
            "batch_number",
            "quantity_received",
            "unit_cost",
            "received_at",
            "expiry_date",
            "notes",
        ]
        widgets = {
            "received_at": forms.DateInput(attrs={"type": "date"}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["stock_item"].queryset = StockItem.objects.filter(
            is_active=True
        ).order_by("name")
        self.fields["supplier"].queryset = Supplier.objects.filter(
            is_active=True
        ).order_by("name")

        self.apply_bootstrap_classes()


class StockAdjustmentForm(BootstrapFormMixin, forms.Form):
    adjustment_type = forms.ChoiceField(
        choices=[
            (StockMovementType.ADJUSTMENT_IN, "Adjustment In"),
            (StockMovementType.ADJUSTMENT_OUT, "Adjustment Out"),
            (StockMovementType.DAMAGED, "Damaged"),
            (StockMovementType.EXPIRED, "Expired"),
        ]
    )
    quantity = forms.DecimalField(min_value=0.01, decimal_places=2)
    reason = forms.CharField(widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class InventoryUsageForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = InventoryUsage
        fields = [
            "usage_context",
            "title",
            "demonstration_session",
            "self_practice_session",
            "osce_exam",
            "notes",
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["demonstration_session"].queryset = (
            DemonstrationSession.objects.select_related(
                "module_offering",
                "module_offering__module",
            ).order_by("-booking__start_at")
        )
        self.fields["self_practice_session"].queryset = (
            SelfPracticeSession.objects.select_related(
                "module_offering",
                "module_offering__module",
                "student",
            ).order_by("-booking__start_at")
        )
        self.fields["osce_exam"].queryset = OSCEExam.objects.select_related(
            "module_offering",
            "module_offering__module",
        ).order_by("-exam_date")

        self.apply_bootstrap_classes()

    def clean(self):
        cleaned_data = super().clean()

        context = cleaned_data.get("usage_context")
        demonstration_session = cleaned_data.get("demonstration_session")
        self_practice_session = cleaned_data.get("self_practice_session")
        osce_exam = cleaned_data.get("osce_exam")

        selected = [
            demonstration_session,
            self_practice_session,
            osce_exam,
        ]

        if sum(1 for value in selected if value) > 1:
            raise forms.ValidationError(
                "Select only one linked demonstration, self-practice session, or OSCE exam."
            )

        if context == InventoryUsageContext.DEMONSTRATION and not demonstration_session:
            raise forms.ValidationError(
                "Select a demonstration session for demonstration usage."
            )

        if context == InventoryUsageContext.SELF_PRACTICE and not self_practice_session:
            raise forms.ValidationError(
                "Select a self-practice session for self-practice usage."
            )

        if context == InventoryUsageContext.OSCE and not osce_exam:
            raise forms.ValidationError("Select an OSCE exam for OSCE usage.")

        return cleaned_data


class InventoryUsageItemForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = InventoryUsageItem
        fields = [
            "stock_item",
            "quantity_requested",
            "quantity_approved",
            "remarks",
        ]

    def __init__(self, *args, **kwargs):
        self.is_approval = kwargs.pop("is_approval", False)
        super().__init__(*args, **kwargs)

        self.fields["stock_item"].queryset = StockItem.objects.filter(
            is_active=True
        ).order_by("name")

        if not self.is_approval:
            self.fields["quantity_approved"].disabled = True
            self.fields["quantity_approved"].required = False

        self.apply_bootstrap_classes()


class InventoryUsageSubmitForm(BootstrapFormMixin, forms.Form):
    confirm = forms.BooleanField(
        label="I confirm this usage is ready for approval.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class InventoryUsageRejectForm(BootstrapFormMixin, forms.Form):
    reason = forms.CharField(widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()