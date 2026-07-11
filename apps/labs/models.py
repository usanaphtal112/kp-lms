from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from django.utils import timezone


class LabRoom(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=150, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class SessionStatus(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Scheduled"
    ONGOING = "ONGOING", "Ongoing"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


class DemonstrationSession(models.Model):
    booking = models.OneToOneField(
        "bookings.LabBooking",
        on_delete=models.CASCADE,
        related_name="demonstration_session",
    )
    module_offering = models.ForeignKey(
        "academics.ModuleOffering",
        on_delete=models.PROTECT,
        related_name="demonstration_sessions",
    )
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="demonstration_sessions",
        limit_choices_to={"role": "LECTURER"},
    )
    topic = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=30,
        choices=SessionStatus.choices,
        default=SessionStatus.SCHEDULED,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["booking__start_at"]

    def clean(self):
        super().clean()

        if self.booking_id and self.module_offering_id:
            if self.booking.module_offering_id != self.module_offering_id:
                raise ValidationError(
                    "Demonstration session must use the same module offering as its booking."
                )

    def __str__(self):
        return f"{self.topic} - {self.module_offering}"


class DemonstrationProcedure(models.Model):
    demonstration_session = models.ForeignKey(
        DemonstrationSession,
        on_delete=models.CASCADE,
        related_name="session_procedures",
    )
    procedure = models.ForeignKey(
        "academics.Procedure",
        on_delete=models.PROTECT,
        related_name="demonstration_sessions",
    )

    class Meta:
        ordering = ["procedure__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["demonstration_session", "procedure"],
                name="unique_procedure_per_demonstration_session",
            ),
        ]

    def clean(self):
        super().clean()

        if self.demonstration_session_id and self.procedure_id:
            if self.procedure.module_id != self.demonstration_session.module_offering.module_id:
                raise ValidationError(
                    "Procedure must belong to the same module as the demonstration session."
                )

    def __str__(self):
        return f"{self.demonstration_session} - {self.procedure}"
    

class SelfPracticeSession(models.Model):
    booking = models.OneToOneField(
        "bookings.LabBooking",
        on_delete=models.CASCADE,
        related_name="self_practice_session",
    )
    module_offering = models.ForeignKey(
        "academics.ModuleOffering",
        on_delete=models.PROTECT,
        related_name="self_practice_sessions",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="self_practice_sessions",
        limit_choices_to={"role": "STUDENT"},
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="supervised_self_practice_sessions",
        null=True,
        blank=True,
        limit_choices_to={
            "role__in": [
                "LECTURER",
                "LAB_COORDINATOR",
                "ADMINISTRATION",
                "IT_ADMIN",
            ]
        },
    )
    objectives = models.TextField(blank=True)
    status = models.CharField(
        max_length=30,
        choices=SessionStatus.choices,
        default=SessionStatus.SCHEDULED,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["booking__start_at"]
        indexes = [
            models.Index(fields=["status"]),
        ]

    def clean(self):
        super().clean()

        if self.booking_id:
            if self.booking.booking_type != "SELF_PRACTICE":
                raise ValidationError(
                    "Self-practice session must be attached to a self-practice booking."
                )

            if self.booking.module_offering_id != self.module_offering_id:
                raise ValidationError(
                    "Self-practice session must use the same module offering as its booking."
                )

            if self.booking.requested_by_id != self.student_id:
                raise ValidationError(
                    "The booking requester must be the same student."
                )

        if self.student_id and getattr(self.student, "role", None) != "STUDENT":
            raise ValidationError("Only student users can request self-practice.")

    def __str__(self):
        return f"{self.student} - {self.module_offering} - {self.booking.start_at}"


class SelfPracticeProcedure(models.Model):
    self_practice_session = models.ForeignKey(
        SelfPracticeSession,
        on_delete=models.CASCADE,
        related_name="planned_procedures",
    )
    procedure = models.ForeignKey(
        "academics.Procedure",
        on_delete=models.PROTECT,
        related_name="self_practice_sessions",
    )

    class Meta:
        ordering = ["procedure__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["self_practice_session", "procedure"],
                name="unique_procedure_per_self_practice_session",
            ),
        ]

    def clean(self):
        super().clean()

        if self.self_practice_session_id and self.procedure_id:
            if self.procedure.module_id != self.self_practice_session.module_offering.module_id:
                raise ValidationError(
                    "Procedure must belong to the same module as the self-practice session."
                )

    def __str__(self):
        return f"{self.self_practice_session} - {self.procedure}"


class ProcedureLogStatus(models.TextChoices):
    PENDING = "PENDING", "Pending verification"
    VERIFIED = "VERIFIED", "Verified"
    REJECTED = "REJECTED", "Rejected"


class ProcedureLog(models.Model):
    self_practice_session = models.ForeignKey(
        SelfPracticeSession,
        on_delete=models.CASCADE,
        related_name="procedure_logs",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="procedure_logs",
        limit_choices_to={"role": "STUDENT"},
    )
    module_offering = models.ForeignKey(
        "academics.ModuleOffering",
        on_delete=models.PROTECT,
        related_name="procedure_logs",
    )
    procedure = models.ForeignKey(
        "academics.Procedure",
        on_delete=models.PROTECT,
        related_name="procedure_logs",
    )
    performed_count = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=30,
        choices=ProcedureLogStatus.choices,
        default=ProcedureLogStatus.PENDING,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="verified_procedure_logs",
        null=True,
        blank=True,
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "-created_at",
            "procedure__code",
        ]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def clean(self):
        super().clean()

        if self.student_id and self.self_practice_session_id:
            if self.self_practice_session.student_id != self.student_id:
                raise ValidationError(
                    "Procedure log student must match the self-practice session student."
                )

        if self.module_offering_id and self.self_practice_session_id:
            if self.self_practice_session.module_offering_id != self.module_offering_id:
                raise ValidationError(
                    "Procedure log module offering must match the self-practice session."
                )

        if self.procedure_id and self.module_offering_id:
            if self.procedure.module_id != self.module_offering.module_id:
                raise ValidationError(
                    "Procedure must belong to the selected module offering."
                )

    def mark_verified(self, verified_by, remarks=""):
        self.status = ProcedureLogStatus.VERIFIED
        self.verified_by = verified_by
        self.verified_at = timezone.now()

        if remarks:
            self.remarks = remarks

    def mark_rejected(self, verified_by, remarks=""):
        self.status = ProcedureLogStatus.REJECTED
        self.verified_by = verified_by
        self.verified_at = timezone.now()

        if remarks:
            self.remarks = remarks

    def __str__(self):
        return f"{self.student} - {self.procedure} - {self.status}"