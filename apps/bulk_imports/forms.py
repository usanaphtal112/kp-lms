from pathlib import Path

from django import forms
from django.conf import settings

from .models import ImporterType
from .parsers import ALLOWED_EXTENSIONS


class BulkImportUploadForm(forms.Form):
    importer_type = forms.ChoiceField(choices=ImporterType.choices)
    file = forms.FileField(
        help_text="Upload a .csv or .xlsx file with the required headers.",
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

        self.fields["importer_type"].widget.attrs["class"] = "form-select"

    def clean_importer_type(self):
        importer_type = self.cleaned_data["importer_type"]

        if importer_type in {ImporterType.STUDENTS, ImporterType.STAFF}:
            if getattr(self.user, "role", None) != "IT_ADMIN" and not self.user.is_superuser:
                raise forms.ValidationError(
                    "Only IT Administrators can bulk import students or staff."
                )

        return importer_type

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]

        extension = Path(uploaded_file.name).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise forms.ValidationError("Only .csv and .xlsx files are allowed.")

        max_size = settings.KPLMS_MAX_IMPORT_FILE_SIZE_MB * 1024 * 1024

        if uploaded_file.size > max_size:
            raise forms.ValidationError(
                f"File is too large. Maximum size is "
                f"{settings.KPLMS_MAX_IMPORT_FILE_SIZE_MB} MB."
            )

        return uploaded_file