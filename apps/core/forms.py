from django import forms


class BootstrapFilterFormMixin:
    def apply_bootstrap_classes(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                css_class = "form-select"
            else:
                css_class = "form-control"

            existing_classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_classes} {css_class}".strip()