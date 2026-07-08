from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models
from django.utils import timezone

class UserRole(models.TextChoices):
    IT_ADMIN = "IT_ADMIN", "IT Administrator"
    LECTURER = "LECTURER", "Lecturer"
    LAB_COORDINATOR = "LAB_COORDINATOR", "Skills Lab Coordinator"
    ADMINISTRATION = "ADMINISTRATION", "Administration"
    STUDENT = "STUDENT", "Student"

class CustomUserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.IT_ADMIN)
        extra_fields.setdefault("must_change_password", False)

        return super().create_superuser(
            username=username,
            email=email,
            password=password,
            **extra_fields,
        )

class User(AbstractUser):
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        db_index=True,
    )
    phone_number = models.CharField(max_length=30, blank=True)
    must_change_password = models.BooleanField(default=True)

    objects = CustomUserManager()

    class Meta:
        ordering = ["first_name", "last_name", "username"]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["username"]),
            models.Index(fields=["is_active"]),
        ]

    def is_it_admin(self):
        return self.role == UserRole.IT_ADMIN

    def is_lecturer(self):
        return self.role == UserRole.LECTURER

    def is_lab_coordinator(self):
        return self.role == UserRole.LAB_COORDINATOR

    def is_administration(self):
        return self.role == UserRole.ADMINISTRATION

    def is_student(self):
        return self.role == UserRole.STUDENT
    
class StudentType(models.TextChoices):
    REGULAR = "REGULAR", "Regular"
    UPGRADING = "UPGRADING", "Upgrading"
    CREDIT_TRANSFER = "CREDIT_TRANSFER", "Credit Transfer"
    CONTINUING = "CONTINUING", "Continuing"


class StudentAcademicStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    SUSPENDED = "SUSPENDED", "Suspended"
    GRADUATED = "GRADUATED", "Graduated"
    WITHDRAWN = "WITHDRAWN", "Withdrawn"


class YearLevel(models.IntegerChoices):
    YEAR_1 = 1, "Year I"
    YEAR_2 = 2, "Year II"
    YEAR_3 = 3, "Year III"
    YEAR_4 = 4, "Year IV"


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    registration_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
    )
    student_type = models.CharField(
        max_length=30,
        choices=StudentType.choices,
        default=StudentType.REGULAR,
    )
    academic_status = models.CharField(
        max_length=30,
        choices=StudentAcademicStatus.choices,
        default=StudentAcademicStatus.ACTIVE,
    )
    current_academic_level = models.PositiveSmallIntegerField(
        choices=YearLevel.choices,
        default=YearLevel.YEAR_1,
    )
    admission_year = models.PositiveSmallIntegerField(null=True, blank=True)
    is_active_student = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["registration_number"]
        indexes = [
            models.Index(fields=["registration_number"]),
            models.Index(fields=["student_type"]),
            models.Index(fields=["academic_status"]),
        ]

    def __str__(self):
        return self.registration_number


class StaffProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_profile",
    )
    staff_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
    )
    job_title = models.CharField(max_length=120, blank=True)
    department_name = models.CharField(max_length=120, blank=True)
    office_location = models.CharField(max_length=120, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__first_name", "user__last_name"]
        indexes = [
            models.Index(fields=["staff_number"]),
            models.Index(fields=["department_name"]),
        ]

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class AccountAction(models.TextChoices):
    CREATED = "CREATED", "Created"
    UPDATED = "UPDATED", "Updated"
    ACTIVATED = "ACTIVATED", "Activated"
    DEACTIVATED = "DEACTIVATED", "Deactivated"
    PASSWORD_RESET = "PASSWORD_RESET", "Password reset"
    ROLE_CHANGED = "ROLE_CHANGED", "Role changed"


class AccountActionLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="account_actions_performed",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="account_action_logs",
    )
    action = models.CharField(max_length=40, choices=AccountAction.choices)
    message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.action} - {self.target_user}"
    
class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    registration_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
    )
    student_type = models.CharField(
        max_length=30,
        choices=StudentType.choices,
        default=StudentType.REGULAR,
    )
    academic_status = models.CharField(
        max_length=30,
        choices=StudentAcademicStatus.choices,
        default=StudentAcademicStatus.ACTIVE,
    )
    current_academic_level = models.PositiveSmallIntegerField(
        choices=YearLevel.choices,
        default=YearLevel.YEAR_1,
    )
    admission_year = models.PositiveSmallIntegerField(null=True, blank=True)

    program = models.ForeignKey(
        "academics.Program",
        on_delete=models.PROTECT,
        related_name="student_profiles",
        null=True,
        blank=True,
    )
    cohort = models.ForeignKey(
        "academics.Cohort",
        on_delete=models.PROTECT,
        related_name="student_profiles",
        null=True,
        blank=True,
    )

    is_active_student = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()

        if self.program and self.cohort and self.cohort.program_id != self.program_id:
            from django.core.exceptions import ValidationError

            raise ValidationError(
                "Selected cohort does not belong to the selected program."
            )