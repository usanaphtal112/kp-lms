from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class OSCEExamStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    READY = "READY", "Ready"
    ONGOING = "ONGOING", "Ongoing"
    COMPLETED = "COMPLETED", "Completed"
    RESULTS_APPROVED = "RESULTS_APPROVED", "Results Approved"
    PUBLISHED = "PUBLISHED", "Published"
    CANCELLED = "CANCELLED", "Cancelled"


class OSCEExam(models.Model):
    module_offering = models.ForeignKey(
        "academics.ModuleOffering",
        on_delete=models.PROTECT,
        related_name="osce_exams",
    )
    title = models.CharField(max_length=180)
    exam_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    status = models.CharField(
        max_length=40,
        choices=OSCEExamStatus.choices,
        default=OSCEExamStatus.DRAFT,
        db_index=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_osce_exams",
        null=True,
        blank=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_osce_exams",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="published_osce_exams",
        null=True,
        blank=True,
    )
    published_at = models.DateTimeField(null=True, blank=True)

    instructions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-exam_date", "module_offering__module__code"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["exam_date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["module_offering", "title", "exam_date"],
                name="unique_osce_exam_per_module_title_date",
            ),
        ]

    def __str__(self):
        return f"{self.title} - {self.module_offering}"


class OSCEStation(models.Model):
    osce_exam = models.ForeignKey(
        OSCEExam,
        on_delete=models.CASCADE,
        related_name="stations",
    )
    procedure = models.ForeignKey(
        "academics.Procedure",
        on_delete=models.PROTECT,
        related_name="osce_stations",
    )
    title = models.CharField(max_length=180)
    station_order = models.PositiveSmallIntegerField(default=1)
    duration_minutes = models.PositiveSmallIntegerField(default=10)
    max_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("100.00"),
    )
    instructions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["osce_exam", "station_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["osce_exam", "station_order"],
                name="unique_station_order_per_osce_exam",
            ),
            models.UniqueConstraint(
                fields=["osce_exam", "procedure"],
                name="unique_procedure_per_osce_exam",
            ),
            models.CheckConstraint(
                condition=Q(max_score__gt=0),
                name="osce_station_max_score_greater_than_zero",
            ),
        ]

    def clean(self):
        super().clean()

        if self.osce_exam_id and self.procedure_id:
            if self.procedure.module_id != self.osce_exam.module_offering.module_id:
                raise ValidationError(
                    "Station procedure must belong to the same module as the OSCE exam."
                )

    def __str__(self):
        return f"{self.osce_exam} - Station {self.station_order}: {self.title}"


class OSCERubricItem(models.Model):
    station = models.ForeignKey(
        OSCEStation,
        on_delete=models.CASCADE,
        related_name="rubric_items",
    )
    criterion = models.CharField(max_length=255)
    max_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )
    item_order = models.PositiveSmallIntegerField(default=1)
    is_critical = models.BooleanField(default=False)

    class Meta:
        ordering = ["station", "item_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["station", "item_order"],
                name="unique_rubric_item_order_per_station",
            ),
            models.CheckConstraint(
                condition=Q(max_score__gt=0),
                name="rubric_item_max_score_greater_than_zero",
            ),
        ]

    def __str__(self):
        return f"{self.station} - {self.criterion}"


class AttemptType(models.TextChoices):
    FIRST_ATTEMPT = "FIRST_ATTEMPT", "First Attempt"
    RETAKE = "RETAKE", "Retake"


class AttemptStatus(models.TextChoices):
    CREATED = "CREATED", "Created"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    SUBMITTED = "SUBMITTED", "Submitted"
    CALCULATED = "CALCULATED", "Calculated"
    APPROVED = "APPROVED", "Approved"
    PUBLISHED = "PUBLISHED", "Published"
    CANCELLED = "CANCELLED", "Cancelled"


class OSCEAttempt(models.Model):
    osce_exam = models.ForeignKey(
        OSCEExam,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="osce_attempts",
        limit_choices_to={"role": "STUDENT"},
    )
    attempt_number = models.PositiveSmallIntegerField(default=1)
    attempt_type = models.CharField(
        max_length=30,
        choices=AttemptType.choices,
        default=AttemptType.FIRST_ATTEMPT,
    )
    status = models.CharField(
        max_length=30,
        choices=AttemptStatus.choices,
        default=AttemptStatus.CREATED,
        db_index=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_osce_attempts",
        null=True,
        blank=True,
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="submitted_osce_attempts",
        null=True,
        blank=True,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)

    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "osce_exam",
            "student__student_profile__registration_number",
            "attempt_number",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["osce_exam", "student", "attempt_number"],
                name="unique_osce_attempt_number_per_student_exam",
            ),
        ]
        indexes = [
            models.Index(fields=["attempt_type"]),
            models.Index(fields=["status"]),
        ]

    def clean(self):
        super().clean()

        if self.student_id and getattr(self.student, "role", None) != "STUDENT":
            raise ValidationError("Only students can have OSCE attempts.")

    def __str__(self):
        return f"{self.student} - {self.osce_exam} - Attempt {self.attempt_number}"


class OSCEScore(models.Model):
    attempt = models.ForeignKey(
        OSCEAttempt,
        on_delete=models.CASCADE,
        related_name="scores",
    )
    station = models.ForeignKey(
        OSCEStation,
        on_delete=models.CASCADE,
        related_name="scores",
    )
    rubric_item = models.ForeignKey(
        OSCERubricItem,
        on_delete=models.CASCADE,
        related_name="scores",
    )
    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="marked_osce_scores",
        null=True,
        blank=True,
    )
    marked_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["attempt", "station__station_order", "rubric_item__item_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "rubric_item"],
                name="unique_score_per_attempt_rubric_item",
            ),
            models.CheckConstraint(
                condition=Q(score__gte=0),
                name="osce_score_greater_or_equal_zero",
            ),
        ]

    def clean(self):
        super().clean()

        if self.station_id and self.rubric_item_id:
            if self.rubric_item.station_id != self.station_id:
                raise ValidationError(
                    "Rubric item must belong to the selected station."
                )

        if self.attempt_id and self.station_id:
            if self.station.osce_exam_id != self.attempt.osce_exam_id:
                raise ValidationError(
                    "Station must belong to the same OSCE exam as the attempt."
                )

        if self.rubric_item_id and self.score is not None:
            if self.score > self.rubric_item.max_score:
                raise ValidationError(
                    "Score cannot be greater than the rubric item maximum score."
                )

    def __str__(self):
        return f"{self.attempt} - {self.rubric_item} - {self.score}"


class OSCEResult(models.Model):
    attempt = models.OneToOneField(
        OSCEAttempt,
        on_delete=models.CASCADE,
        related_name="result",
    )

    total_score = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total_possible_score = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    final_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    pass_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("60.00"),
    )
    is_passed = models.BooleanField(default=False)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_osce_results",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    calculated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = [
            "attempt__osce_exam",
            "attempt__student__student_profile__registration_number",
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(percentage__gte=0) & Q(percentage__lte=100),
                name="osce_percentage_between_0_and_100",
            ),
            models.CheckConstraint(
                condition=Q(final_mark__gte=0) & Q(final_mark__lte=100),
                name="osce_final_mark_between_0_and_100",
            ),
        ]

    def __str__(self):
        return f"{self.attempt} - {self.final_mark}%"


class RetakeRequestStatus(models.TextChoices):
    REQUESTED = "REQUESTED", "Requested"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    CANCELLED = "CANCELLED", "Cancelled"


class RetakeRequest(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="retake_requests",
        limit_choices_to={"role": "STUDENT"},
    )
    osce_exam = models.ForeignKey(
        OSCEExam,
        on_delete=models.CASCADE,
        related_name="retake_requests",
    )
    original_attempt = models.ForeignKey(
        OSCEAttempt,
        on_delete=models.PROTECT,
        related_name="retake_requests",
    )
    reason = models.TextField()
    status = models.CharField(
        max_length=30,
        choices=RetakeRequestStatus.choices,
        default=RetakeRequestStatus.REQUESTED,
        db_index=True,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_retake_requests",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True)

    created_attempt = models.OneToOneField(
        OSCEAttempt,
        on_delete=models.SET_NULL,
        related_name="source_retake_request",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "osce_exam", "original_attempt"],
                name="unique_retake_request_per_failed_attempt",
            ),
        ]

    def clean(self):
        super().clean()

        if self.original_attempt_id:
            if self.original_attempt.student_id != self.student_id:
                raise ValidationError(
                    "Original attempt must belong to the requesting student."
                )

            if self.original_attempt.osce_exam_id != self.osce_exam_id:
                raise ValidationError(
                    "Original attempt must belong to the selected OSCE exam."
                )

            if hasattr(self.original_attempt, "result"):
                if self.original_attempt.result.is_passed:
                    raise ValidationError(
                        "Retake request is only allowed for failed attempts."
                    )

    def __str__(self):
        return f"{self.student} - {self.osce_exam} - {self.status}"
    
class OSCEMarkAuditLog(models.Model):
    score = models.ForeignKey(
        OSCEScore,
        on_delete=models.CASCADE,
        related_name="mark_audit_logs",
        null=True,
        blank=True,
    )
    attempt = models.ForeignKey(
        OSCEAttempt,
        on_delete=models.CASCADE,
        related_name="mark_audit_logs",
    )
    rubric_item = models.ForeignKey(
        OSCERubricItem,
        on_delete=models.SET_NULL,
        related_name="mark_audit_logs",
        null=True,
        blank=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="osce_mark_changes",
        null=True,
        blank=True,
    )
    old_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    new_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.attempt} - {self.rubric_item} - {self.old_score} → {self.new_score}"