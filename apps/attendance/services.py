from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from apps.academics.models import (
    ModuleEnrollment,
    ModuleEnrollmentStatus,
    ModuleOffering,
)
from apps.bookings.models import BookingStatus
from apps.labs.models import DemonstrationSession, SessionStatus

from .models import (
    AttendanceChangeLog,
    AttendanceRecord,
    AttendanceStatus,
    EligibilitySnapshot,
)


ATTENDED_STATUSES = {
    AttendanceStatus.PRESENT,
    AttendanceStatus.LATE,
}


def quantize_percentage(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_completed_demonstration_sessions(module_offering):
    return DemonstrationSession.objects.select_related(
        "booking",
        "module_offering",
        "module_offering__module",
    ).filter(
        module_offering=module_offering,
        booking__status=BookingStatus.COMPLETED,
        status=SessionStatus.COMPLETED,
    )


def get_enrolled_students(module_offering):
    return (
        ModuleEnrollment.objects.select_related(
            "student",
            "student__student_profile",
        )
        .filter(
            module_offering=module_offering,
            is_active=True,
            status__in=[
                ModuleEnrollmentStatus.ENROLLED,
                ModuleEnrollmentStatus.IN_PROGRESS,
                ModuleEnrollmentStatus.COMPLETED,
            ],
        )
        .order_by(
            "student__student_profile__registration_number",
            "student__first_name",
            "student__last_name",
        )
    )


def get_attendance_rows_for_session(session):
    enrollments = get_enrolled_students(session.module_offering)

    existing_records = {
        record.student_id: record
        for record in AttendanceRecord.objects.filter(
            demonstration_session=session
        ).select_related(
            "student",
            "student__student_profile",
        )
    }

    rows = []

    for enrollment in enrollments:
        student = enrollment.student
        record = existing_records.get(student.id)

        rows.append(
            {
                "student": student,
                "enrollment": enrollment,
                "record": record,
                "status": record.status if record else AttendanceStatus.UNMARKED,
                "remarks": record.remarks if record else "",
            }
        )

    return rows


@transaction.atomic
def record_session_attendance(
    *,
    session,
    attendance_data,
    recorded_by,
    mark_session_completed=True,
):
    updated_count = 0
    created_count = 0

    for student_id, payload in attendance_data.items():
        status = payload.get("status", AttendanceStatus.UNMARKED)
        remarks = payload.get("remarks", "")

        record, created = AttendanceRecord.objects.select_for_update().get_or_create(
            student_id=student_id,
            demonstration_session=session,
            defaults={
                "status": AttendanceStatus.UNMARKED,
            },
        )

        old_status = record.status
        old_remarks = record.remarks

        record.mark(
            status=status,
            recorded_by=recorded_by,
            remarks=remarks,
        )
        record.full_clean()
        record.save(
            update_fields=[
                "status",
                "recorded_by",
                "recorded_at",
                "remarks",
                "updated_at",
            ]
        )

        if created:
            created_count += 1
        else:
            updated_count += 1

        if old_status != status or old_remarks != remarks:
            AttendanceChangeLog.objects.create(
                attendance_record=record,
                actor=recorded_by,
                old_status=old_status,
                new_status=status,
                old_remarks=old_remarks,
                new_remarks=remarks,
                change_reason="Attendance marked from session screen.",
            )

    if mark_session_completed:
        session.status = SessionStatus.COMPLETED
        session.save(update_fields=["status", "updated_at"])

        booking = session.booking
        booking.status = BookingStatus.COMPLETED
        booking.save(update_fields=["status", "updated_at"])

    refresh_module_offering_eligibility(session.module_offering)

    return {
        "created_count": created_count,
        "updated_count": updated_count,
    }


def calculate_student_module_attendance(student, module_offering):
    sessions = list(get_completed_demonstration_sessions(module_offering))

    records = {
        record.demonstration_session_id: record
        for record in AttendanceRecord.objects.filter(
            student=student,
            demonstration_session__in=sessions,
        )
    }

    total_completed_sessions = len(sessions)
    denominator = 0
    attended_sessions = 0
    excused_sessions = 0
    absent_sessions = 0
    unmarked_sessions = 0

    for session in sessions:
        record = records.get(session.id)
        status = record.status if record else AttendanceStatus.UNMARKED

        if status == AttendanceStatus.EXCUSED:
            excused_sessions += 1
            continue

        denominator += 1

        if status in ATTENDED_STATUSES:
            attended_sessions += 1
        elif status == AttendanceStatus.ABSENT:
            absent_sessions += 1
        elif status == AttendanceStatus.UNMARKED:
            unmarked_sessions += 1

    if denominator == 0:
        percentage = Decimal("0.00")
    else:
        percentage = (
            Decimal(attended_sessions) / Decimal(denominator)
        ) * Decimal("100.00")

    percentage = quantize_percentage(percentage)
    required_percentage = module_offering.module.attendance_requirement

    is_eligible = (
        denominator > 0
        and percentage >= required_percentage
    )

    return {
        "student": student,
        "module_offering": module_offering,
        "total_completed_sessions": total_completed_sessions,
        "denominator": denominator,
        "attended_sessions": attended_sessions,
        "excused_sessions": excused_sessions,
        "absent_sessions": absent_sessions,
        "unmarked_sessions": unmarked_sessions,
        "attendance_percentage": percentage,
        "required_percentage": required_percentage,
        "is_self_practice_eligible": is_eligible,
        "is_osce_eligible": is_eligible,
    }


@transaction.atomic
def refresh_eligibility_snapshot(student, module_offering):
    summary = calculate_student_module_attendance(student, module_offering)

    snapshot, _ = EligibilitySnapshot.objects.update_or_create(
        student=student,
        module_offering=module_offering,
        defaults={
            "total_completed_sessions": summary["total_completed_sessions"],
            "attended_sessions": summary["attended_sessions"],
            "excused_sessions": summary["excused_sessions"],
            "absent_sessions": summary["absent_sessions"],
            "unmarked_sessions": summary["unmarked_sessions"],
            "attendance_percentage": summary["attendance_percentage"],
            "required_percentage": summary["required_percentage"],
            "is_self_practice_eligible": summary["is_self_practice_eligible"],
            "is_osce_eligible": summary["is_osce_eligible"],
            "calculated_at": timezone.now(),
        },
    )

    return snapshot


@transaction.atomic
def refresh_module_offering_eligibility(module_offering):
    snapshots = []

    for enrollment in get_enrolled_students(module_offering):
        snapshot = refresh_eligibility_snapshot(
            enrollment.student,
            module_offering,
        )
        snapshots.append(snapshot)

    return snapshots


def get_student_attendance_summaries(student):
    module_offerings = ModuleOffering.objects.select_related(
        "module",
        "cohort",
        "academic_year",
        "semester",
    ).filter(
        enrollments__student=student,
        enrollments__is_active=True,
    ).distinct()

    return [
        calculate_student_module_attendance(student, module_offering)
        for module_offering in module_offerings
    ]