from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class AttendanceStatus(models.TextChoices):
    UNMARKED = "UNMARKED", "Unmarked"
    PRESENT = "PRESENT", "Present"
    ABSENT = "ABSENT", "Absent"
    LATE = "LATE", "Late"
    EXCUSED = "EXCUSED", "Excused"


class AttendanceRecord(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="demonstration_attendance_records",
        limit_choices_to={"role": "STUDENT"},
    )
    demonstration_session = models.ForeignKey(
        "labs.DemonstrationSession",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    status = models.CharField(
        max_length=30,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.UNMARKED,
        db_index=True,
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="recorded_demonstration_attendance",
        null=True,
        blank=True,
    )
    recorded_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "demonstration_session__booking__start_at",
            "student__student_profile__registration_number",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "demonstration_session"],
                name="unique_student_attendance_per_demonstration",
            ),
        ]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["recorded_at"]),
        ]

    def clean(self):
        super().clean()

        if self.student_id and getattr(self.student, "role", None) != "STUDENT":
            raise ValidationError("Only student users can have attendance records.")

        if self.student_id and self.demonstration_session_id:
            enrolled = self.student.module_enrollments.filter(
                module_offering=self.demonstration_session.module_offering,
                is_active=True,
            ).exists()

            if not enrolled:
                raise ValidationError(
                    "Student is not enrolled in this demonstration's module offering."
                )

    def mark(self, *, status, recorded_by, remarks=""):
        self.status = status
        self.recorded_by = recorded_by
        self.recorded_at = timezone.now()
        self.remarks = remarks

    def __str__(self):
        return f"{self.student} - {self.demonstration_session} - {self.status}"


class EligibilitySnapshot(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="eligibility_snapshots",
        limit_choices_to={"role": "STUDENT"},
    )
    module_offering = models.ForeignKey(
        "academics.ModuleOffering",
        on_delete=models.CASCADE,
        related_name="eligibility_snapshots",
    )

    total_completed_sessions = models.PositiveIntegerField(default=0)
    attended_sessions = models.PositiveIntegerField(default=0)
    excused_sessions = models.PositiveIntegerField(default=0)
    absent_sessions = models.PositiveIntegerField(default=0)
    unmarked_sessions = models.PositiveIntegerField(default=0)

    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    required_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("80.00"),
    )

    is_self_practice_eligible = models.BooleanField(default=False)
    is_osce_eligible = models.BooleanField(default=False)

    calculated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = [
            "module_offering",
            "student__student_profile__registration_number",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "module_offering"],
                name="unique_eligibility_snapshot_per_student_offering",
            ),
            models.CheckConstraint(
                condition=Q(attendance_percentage__gte=0)
                & Q(attendance_percentage__lte=100),
                name="eligibility_percentage_between_0_and_100",
            ),
        ]

    def __str__(self):
        return f"{self.student} - {self.module_offering} - {self.attendance_percentage}%"


class AttendanceChangeLog(models.Model):
    attendance_record = models.ForeignKey(
        AttendanceRecord,
        on_delete=models.CASCADE,
        related_name="change_logs",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="attendance_changes",
        null=True,
        blank=True,
    )
    old_status = models.CharField(
        max_length=30,
        choices=AttendanceStatus.choices,
        blank=True,
    )
    new_status = models.CharField(
        max_length=30,
        choices=AttendanceStatus.choices,
    )
    old_remarks = models.TextField(blank=True)
    new_remarks = models.TextField(blank=True)
    change_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.attendance_record} changed by {self.actor}"
    

class SelfPracticeAttendanceRecord(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="self_practice_attendance_records",
        limit_choices_to={"role": "STUDENT"},
    )
    self_practice_session = models.OneToOneField(
        "labs.SelfPracticeSession",
        on_delete=models.CASCADE,
        related_name="attendance_record",
    )
    status = models.CharField(
        max_length=30,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.UNMARKED,
        db_index=True,
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="recorded_self_practice_attendance",
        null=True,
        blank=True,
    )
    recorded_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["recorded_at"]),
        ]

    def clean(self):
        super().clean()

        if self.student_id and self.self_practice_session_id:
            if self.self_practice_session.student_id != self.student_id:
                raise ValidationError(
                    "Attendance student must match the self-practice session student."
                )

    def mark(self, *, status, recorded_by, remarks=""):
        self.status = status
        self.recorded_by = recorded_by
        self.recorded_at = timezone.now()
        self.remarks = remarks

    def __str__(self):
        return f"{self.student} - {self.self_practice_session} - {self.status}"