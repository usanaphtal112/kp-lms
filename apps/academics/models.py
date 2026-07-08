from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class AcademicBaseModel(models.Model):
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Faculty(AcademicBaseModel):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "faculties"

    def __str__(self):
        return self.name


class Department(AcademicBaseModel):
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.PROTECT,
        related_name="departments",
    )
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["faculty__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["faculty", "code"],
                name="unique_department_code_per_faculty",
            ),
            models.UniqueConstraint(
                fields=["faculty", "name"],
                name="unique_department_name_per_faculty",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.faculty.code})"


class AwardType(models.TextChoices):
    CERTIFICATE = "CERTIFICATE", "Certificate"
    DIPLOMA = "DIPLOMA", "Diploma"
    ADVANCED_DIPLOMA = "ADVANCED_DIPLOMA", "Advanced Diploma"
    BACHELOR = "BACHELOR", "Bachelor"
    MASTER = "MASTER", "Master"


class Program(AcademicBaseModel):
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="programs",
    )
    name = models.CharField(max_length=180)
    code = models.CharField(max_length=30, unique=True)
    award_type = models.CharField(
        max_length=40,
        choices=AwardType.choices,
        default=AwardType.BACHELOR,
    )
    duration_years = models.PositiveSmallIntegerField(default=3)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["department__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "name"],
                name="unique_program_name_per_department",
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class CohortStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    COMPLETED = "COMPLETED", "Completed"
    SUSPENDED = "SUSPENDED", "Suspended"
    ARCHIVED = "ARCHIVED", "Archived"


class Cohort(AcademicBaseModel):
    program = models.ForeignKey(
        Program,
        on_delete=models.PROTECT,
        related_name="cohorts",
    )
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=50)
    intake_year = models.PositiveSmallIntegerField()
    graduation_year = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=CohortStatus.choices,
        default=CohortStatus.ACTIVE,
    )

    class Meta:
        ordering = ["-intake_year", "program__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["program", "code"],
                name="unique_cohort_code_per_program",
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class AcademicYear(AcademicBaseModel):
    name = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gt=models.F("start_date")),
                name="academic_year_end_after_start",
            ),
            models.UniqueConstraint(
                fields=["is_current"],
                condition=Q(is_current=True),
                name="unique_current_academic_year",
            ),
        ]

    def __str__(self):
        return self.name


class SemesterNumber(models.IntegerChoices):
    SEMESTER_1 = 1, "Semester I"
    SEMESTER_2 = 2, "Semester II"
    SPECIAL = 3, "Special Semester"


class Semester(AcademicBaseModel):
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="semesters",
    )
    name = models.CharField(max_length=80)
    semester_number = models.PositiveSmallIntegerField(
        choices=SemesterNumber.choices,
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-academic_year__start_date", "semester_number"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gt=models.F("start_date")),
                name="semester_end_after_start",
            ),
            models.UniqueConstraint(
                fields=["academic_year", "semester_number"],
                name="unique_semester_number_per_academic_year",
            ),
            models.UniqueConstraint(
                fields=["is_current"],
                condition=Q(is_current=True),
                name="unique_current_semester",
            ),
        ]

    def clean(self):
        super().clean()

        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError("Semester end date must be after start date.")

        if self.academic_year_id:
            if self.start_date < self.academic_year.start_date:
                raise ValidationError("Semester cannot start before the academic year.")

            if self.end_date > self.academic_year.end_date:
                raise ValidationError("Semester cannot end after the academic year.")

    def __str__(self):
        return f"{self.name} - {self.academic_year.name}"


class YearLevel(models.IntegerChoices):
    YEAR_1 = 1, "Year I"
    YEAR_2 = 2, "Year II"
    YEAR_3 = 3, "Year III"
    YEAR_4 = 4, "Year IV"


class Module(AcademicBaseModel):
    program = models.ForeignKey(
        Program,
        on_delete=models.PROTECT,
        related_name="modules",
    )
    code = models.CharField(max_length=50)
    title = models.CharField(max_length=180)
    year_level = models.PositiveSmallIntegerField(choices=YearLevel.choices)
    semester_number = models.PositiveSmallIntegerField(
        choices=SemesterNumber.choices,
    )
    credits = models.PositiveSmallIntegerField(default=0)
    attendance_requirement = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("80.00"),
    )
    pass_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("60.00"),
    )
    description = models.TextField(blank=True)
    prerequisites = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="unlocks_modules",
    )

    class Meta:
        ordering = ["program__name", "year_level", "semester_number", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["program", "code"],
                name="unique_module_code_per_program",
            ),
            models.CheckConstraint(
                condition=Q(attendance_requirement__gte=0)
                & Q(attendance_requirement__lte=100),
                name="module_attendance_requirement_between_0_and_100",
            ),
            models.CheckConstraint(
                condition=Q(pass_mark__gte=0) & Q(pass_mark__lte=100),
                name="module_pass_mark_between_0_and_100",
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.title}"


class ModuleOfferingStatus(models.TextChoices):
    PLANNED = "PLANNED", "Planned"
    ONGOING = "ONGOING", "Ongoing"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


class ModuleOffering(AcademicBaseModel):
    module = models.ForeignKey(
        Module,
        on_delete=models.PROTECT,
        related_name="offerings",
    )
    cohort = models.ForeignKey(
        Cohort,
        on_delete=models.PROTECT,
        related_name="module_offerings",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="module_offerings",
    )
    semester = models.ForeignKey(
        Semester,
        on_delete=models.PROTECT,
        related_name="module_offerings",
    )
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="coordinated_module_offerings",
        null=True,
        blank=True,
        limit_choices_to={
            "role__in": [
                "LECTURER",
                "LAB_COORDINATOR",
                "ADMINISTRATION",
            ]
        },
    )
    status = models.CharField(
        max_length=30,
        choices=ModuleOfferingStatus.choices,
        default=ModuleOfferingStatus.PLANNED,
    )

    class Meta:
        ordering = [
            "-academic_year__start_date",
            "semester__semester_number",
            "module__code",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["module", "cohort", "academic_year", "semester"],
                name="unique_module_offering_per_period",
            ),
        ]

    def clean(self):
        super().clean()

        if self.module_id and self.cohort_id:
            if self.module.program_id != self.cohort.program_id:
                raise ValidationError(
                    "Module and cohort must belong to the same program."
                )

        if self.semester_id and self.academic_year_id:
            if self.semester.academic_year_id != self.academic_year_id:
                raise ValidationError(
                    "Semester must belong to the selected academic year."
                )

    def __str__(self):
        return f"{self.module.code} - {self.cohort.code} - {self.academic_year.name}"


class Procedure(AcademicBaseModel):
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="procedures",
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    minimum_required_practices = models.PositiveSmallIntegerField(default=1)
    is_required = models.BooleanField(default=True)

    class Meta:
        ordering = ["module__code", "code", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["module", "code"],
                name="unique_procedure_code_per_module",
            ),
        ]

    def __str__(self):
        return f"{self.module.code} - {self.name}"


class ProcedureRequirement(AcademicBaseModel):
    module_offering = models.ForeignKey(
        ModuleOffering,
        on_delete=models.CASCADE,
        related_name="procedure_requirements",
    )
    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.PROTECT,
        related_name="offering_requirements",
    )
    required_count = models.PositiveSmallIntegerField(default=1)
    due_date = models.DateField(null=True, blank=True)
    is_mandatory = models.BooleanField(default=True)

    class Meta:
        ordering = ["module_offering", "procedure__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["module_offering", "procedure"],
                name="unique_procedure_requirement_per_offering",
            ),
        ]

    def clean(self):
        super().clean()

        if self.module_offering_id and self.procedure_id:
            if self.procedure.module_id != self.module_offering.module_id:
                raise ValidationError(
                    "Procedure must belong to the same module as the offering."
                )

    def __str__(self):
        return f"{self.module_offering} - {self.procedure.name}"


class EnrollmentType(models.TextChoices):
    NORMAL = "NORMAL", "Normal"
    REPEATING = "REPEATING", "Repeating"
    CREDIT_TRANSFER = "CREDIT_TRANSFER", "Credit Transfer"
    CONTINUING = "CONTINUING", "Continuing"


class ModuleEnrollmentStatus(models.TextChoices):
    ENROLLED = "ENROLLED", "Enrolled"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"
    DROPPED = "DROPPED", "Dropped"
    EXEMPTED = "EXEMPTED", "Exempted"


class ModuleEnrollment(AcademicBaseModel):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="module_enrollments",
        limit_choices_to={"role": "STUDENT"},
    )
    module_offering = models.ForeignKey(
        ModuleOffering,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    enrollment_type = models.CharField(
        max_length=30,
        choices=EnrollmentType.choices,
        default=EnrollmentType.NORMAL,
    )
    status = models.CharField(
        max_length=30,
        choices=ModuleEnrollmentStatus.choices,
        default=ModuleEnrollmentStatus.ENROLLED,
    )
    enrolled_on = models.DateField(default=timezone.localdate)
    completed_on = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["module_offering", "student__first_name", "student__last_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "module_offering"],
                name="unique_student_module_enrollment",
            ),
        ]

    def clean(self):
        super().clean()

        if self.student_id and getattr(self.student, "role", None) != "STUDENT":
            raise ValidationError("Only student users can be enrolled in modules.")

    def __str__(self):
        return f"{self.student} - {self.module_offering}"


class CreditTransferStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class CreditTransfer(AcademicBaseModel):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="credit_transfers",
        limit_choices_to={"role": "STUDENT"},
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.PROTECT,
        related_name="credit_transfers",
    )
    previous_institution = models.CharField(max_length=180)
    previous_module_name = models.CharField(max_length=180)
    previous_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    supporting_file = models.FileField(
        upload_to="credit-transfers/",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=30,
        choices=CreditTransferStatus.choices,
        default=CreditTransferStatus.PENDING,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_credit_transfers",
        null=True,
        blank=True,
        limit_choices_to={
            "role__in": [
                "IT_ADMIN",
                "ADMINISTRATION",
            ]
        },
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "module"],
                name="unique_credit_transfer_per_student_module",
            ),
            models.CheckConstraint(
                condition=Q(previous_mark__isnull=True)
                | (Q(previous_mark__gte=0) & Q(previous_mark__lte=100)),
                name="credit_transfer_mark_between_0_and_100",
            ),
        ]

    def clean(self):
        super().clean()

        if self.student_id and getattr(self.student, "role", None) != "STUDENT":
            raise ValidationError("Only student users can receive credit transfer.")

    def __str__(self):
        return f"{self.student} - {self.module}"