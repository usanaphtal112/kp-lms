from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class BookingType(models.TextChoices):
    DEMONSTRATION = "DEMONSTRATION", "Demonstration"
    SELF_PRACTICE = "SELF_PRACTICE", "Self-practice"
    OSCE = "OSCE", "OSCE"


class BookingStatus(models.TextChoices):
    REQUESTED = "REQUESTED", "Requested"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    CANCELLED = "CANCELLED", "Cancelled"
    COMPLETED = "COMPLETED", "Completed"


class LabBooking(models.Model):
    booking_type = models.CharField(
        max_length=30,
        choices=BookingType.choices,
        default=BookingType.DEMONSTRATION,
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_lab_bookings",
    )
    module_offering = models.ForeignKey(
        "academics.ModuleOffering",
        on_delete=models.PROTECT,
        related_name="lab_bookings",
    )
    lab_room = models.ForeignKey(
        "labs.LabRoom",
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    title = models.CharField(max_length=180)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    notes = models.TextField(blank=True)

    status = models.CharField(
        max_length=30,
        choices=BookingStatus.choices,
        default=BookingStatus.REQUESTED,
        db_index=True,
    )

    requested_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_lab_bookings",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["booking_type"]),
            models.Index(fields=["start_at", "end_at"]),
        ]

    def clean(self):
        super().clean()

        if self.start_at and self.end_at and self.start_at >= self.end_at:
            raise ValidationError("Booking end time must be after start time.")

        if self.lab_room_id and self.start_at and self.end_at:
            conflicts = LabBooking.objects.filter(
                lab_room_id=self.lab_room_id,
                start_at__lt=self.end_at,
                end_at__gt=self.start_at,
                status__in=[
                    BookingStatus.REQUESTED,
                    BookingStatus.APPROVED,
                ],
            )

            if self.pk:
                conflicts = conflicts.exclude(pk=self.pk)

            if conflicts.exists():
                raise ValidationError(
                    "This lab room already has a requested or approved booking in that time range."
                )

    def mark_approved(self, approved_by):
        self.status = BookingStatus.APPROVED
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.rejection_reason = ""

    def mark_rejected(self, approved_by, reason):
        self.status = BookingStatus.REJECTED
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.rejection_reason = reason

    def __str__(self):
        return f"{self.title} - {self.lab_room} - {self.start_at}"


class BookingDecisionAction(models.TextChoices):
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    CANCELLED = "CANCELLED", "Cancelled"
    COMPLETED = "COMPLETED", "Completed"


class BookingDecisionLog(models.Model):
    booking = models.ForeignKey(
        LabBooking,
        on_delete=models.CASCADE,
        related_name="decision_logs",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booking_decisions",
    )
    action = models.CharField(
        max_length=30,
        choices=BookingDecisionAction.choices,
    )
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.booking} - {self.action}"