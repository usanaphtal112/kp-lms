from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


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