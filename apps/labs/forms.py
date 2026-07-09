from django import forms

from .models import LabRoom


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