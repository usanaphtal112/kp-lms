from django import forms
from django.contrib.auth import get_user_model

from .models import (
    StaffProfile,
    StudentAcademicStatus,
    StudentProfile,
    StudentType,
    UserRole,
    YearLevel,
)
from .services import (
    build_student_username,
    create_staff_account,
    create_student_account,
    reset_user_password,
)


class BootstrapFormMixin:
    def apply_bootstrap_classes(self):
        for field in self.fields.values():
            widget = field.widget

            if isinstance(widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(widget, forms.Select):
                css_class = "form-select"
            else:
                css_class = "form-control"

            existing_classes = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing_classes} {css_class}".strip()


class UserFilterForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search username, name, email, registration number...",
            }
        ),
    )
    role = forms.ChoiceField(
        required=False,
        choices=[("", "All roles")] + list(UserRole.choices),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[
            ("", "All statuses"),
            ("active", "Active"),
            ("inactive", "Inactive"),
        ],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class StudentAccountCreateForm(BootstrapFormMixin, forms.Form):
    registration_number = forms.CharField(max_length=50)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(max_length=30, required=False)
    student_type = forms.ChoiceField(choices=StudentType.choices)
    academic_status = forms.ChoiceField(choices=StudentAcademicStatus.choices)
    current_academic_level = forms.ChoiceField(choices=YearLevel.choices)
    admission_year = forms.IntegerField(required=False, min_value=2000)

    def __init__(self, *args, **kwargs):
        self.created_by = kwargs.pop("created_by", None)
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()

    def clean_registration_number(self):
        registration_number = self.cleaned_data["registration_number"]
        username = build_student_username(registration_number)

        User = get_user_model()

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                "A user account already exists for this registration number."
            )

        if StudentProfile.objects.filter(
            registration_number=registration_number.strip().replace(" ", "").upper()
        ).exists():
            raise forms.ValidationError(
                "A student profile already exists for this registration number."
            )

        return registration_number

    def save(self):
        return create_student_account(
            registration_number=self.cleaned_data["registration_number"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            email=self.cleaned_data["email"],
            phone_number=self.cleaned_data["phone_number"],
            student_type=self.cleaned_data["student_type"],
            academic_status=self.cleaned_data["academic_status"],
            current_academic_level=self.cleaned_data["current_academic_level"],
            admission_year=self.cleaned_data["admission_year"],
            created_by=self.created_by,
        )


class StaffAccountCreateForm(BootstrapFormMixin, forms.Form):
    STAFF_ROLE_CHOICES = [
        choice for choice in UserRole.choices if choice[0] != UserRole.STUDENT
    ]

    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(max_length=30, required=False)
    role = forms.ChoiceField(choices=STAFF_ROLE_CHOICES)
    staff_number = forms.CharField(max_length=50, required=False)
    job_title = forms.CharField(max_length=120, required=False)
    department_name = forms.CharField(max_length=120, required=False)
    office_location = forms.CharField(max_length=120, required=False)
    initial_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        help_text="Leave blank to use the default temporary password.",
    )

    def __init__(self, *args, **kwargs):
        self.created_by = kwargs.pop("created_by", None)
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()

    def clean_username(self):
        username = self.cleaned_data["username"].strip().lower()

        User = get_user_model()

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already used.")

        return username

    def clean_staff_number(self):
        staff_number = self.cleaned_data.get("staff_number")

        if not staff_number:
            return None

        if StaffProfile.objects.filter(staff_number=staff_number).exists():
            raise forms.ValidationError("This staff number is already used.")

        return staff_number

    def save(self):
        return create_staff_account(
            username=self.cleaned_data["username"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            email=self.cleaned_data["email"],
            phone_number=self.cleaned_data["phone_number"],
            role=self.cleaned_data["role"],
            staff_number=self.cleaned_data["staff_number"],
            job_title=self.cleaned_data["job_title"],
            department_name=self.cleaned_data["department_name"],
            office_location=self.cleaned_data["office_location"],
            initial_password=self.cleaned_data["initial_password"],
            created_by=self.created_by,
        )


class UserUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "role",
            "is_active",
            "must_change_password",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class AdminPasswordResetForm(BootstrapFormMixin, forms.Form):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput,
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput,
    )

    def __init__(self, *args, **kwargs):
        self.target_user = kwargs.pop("target_user")
        self.reset_by = kwargs.pop("reset_by")
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("The two passwords do not match.")

        return cleaned_data

    def save(self):
        return reset_user_password(
            target_user=self.target_user,
            new_password=self.cleaned_data["new_password1"],
            reset_by=self.reset_by,
        )