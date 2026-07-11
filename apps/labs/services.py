from django.db import transaction
from django.utils import timezone

from apps.attendance.models import AttendanceStatus, SelfPracticeAttendanceRecord
from apps.attendance.services import calculate_student_module_attendance
from apps.bookings.models import BookingDecisionAction, BookingDecisionLog
from apps.bookings.models import BookingStatus, BookingType, LabBooking

from .models import (
    ProcedureLog,
    ProcedureLogStatus,
    SelfPracticeProcedure,
    SelfPracticeSession,
    SessionStatus,
)


def is_student_eligible_for_self_practice(student, module_offering):
    summary = calculate_student_module_attendance(
        student,
        module_offering,
    )
    return summary["is_self_practice_eligible"], summary


@transaction.atomic
def create_self_practice_booking(
    *,
    student,
    module_offering,
    lab_room,
    start_at,
    end_at,
    procedures,
    objectives="",
    notes="",
):
    if getattr(student, "role", None) != "STUDENT":
        raise ValueError("Only students can request self-practice.")

    eligible, summary = is_student_eligible_for_self_practice(
        student,
        module_offering,
    )

    if not eligible:
        raise ValueError(
            f"You are not eligible for self-practice yet. "
            f"Current attendance: {summary['attendance_percentage']}%. "
            f"Required: {summary['required_percentage']}%."
        )

    enrollment_exists = student.module_enrollments.filter(
        module_offering=module_offering,
        is_active=True,
    ).exists()

    if not enrollment_exists:
        raise ValueError("You are not enrolled in this module offering.")

    booking = LabBooking(
        booking_type=BookingType.SELF_PRACTICE,
        requested_by=student,
        module_offering=module_offering,
        lab_room=lab_room,
        title=f"Self-practice: {module_offering.module.code}",
        start_at=start_at,
        end_at=end_at,
        notes=notes,
        status=BookingStatus.REQUESTED,
    )
    booking.full_clean()
    booking.save()

    session = SelfPracticeSession(
        booking=booking,
        module_offering=module_offering,
        student=student,
        objectives=objectives,
        status=SessionStatus.SCHEDULED,
    )
    session.full_clean()
    session.save()

    for procedure in procedures:
        planned_procedure = SelfPracticeProcedure(
            self_practice_session=session,
            procedure=procedure,
        )
        planned_procedure.full_clean()
        planned_procedure.save()

    return session


@transaction.atomic
def approve_self_practice_session(
    *,
    session,
    approved_by,
    supervisor=None,
    comments="",
):
    booking = session.booking

    if booking.status != BookingStatus.REQUESTED:
        raise ValueError("Only requested self-practice bookings can be approved.")

    booking.mark_approved(approved_by)
    booking.full_clean()
    booking.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at",
            "rejection_reason",
            "updated_at",
        ]
    )

    if supervisor:
        session.supervisor = supervisor
        session.save(update_fields=["supervisor", "updated_at"])

    BookingDecisionLog.objects.create(
        booking=booking,
        actor=approved_by,
        action=BookingDecisionAction.APPROVED,
        comments=comments,
    )

    return session


@transaction.atomic
def reject_self_practice_session(
    *,
    session,
    rejected_by,
    reason,
):
    booking = session.booking

    if booking.status != BookingStatus.REQUESTED:
        raise ValueError("Only requested self-practice bookings can be rejected.")

    booking.mark_rejected(rejected_by, reason)
    booking.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at",
            "rejection_reason",
            "updated_at",
        ]
    )

    BookingDecisionLog.objects.create(
        booking=booking,
        actor=rejected_by,
        action=BookingDecisionAction.REJECTED,
        comments=reason,
    )

    return session


@transaction.atomic
def record_self_practice_outcome(
    *,
    session,
    recorded_by,
    attendance_status,
    performed_procedures,
    remarks="",
):
    if session.booking.status != BookingStatus.APPROVED:
        raise ValueError("Only approved self-practice sessions can be recorded.")

    attendance_record, _ = SelfPracticeAttendanceRecord.objects.get_or_create(
        self_practice_session=session,
        defaults={
            "student": session.student,
            "status": AttendanceStatus.UNMARKED,
        },
    )

    attendance_record.mark(
        status=attendance_status,
        recorded_by=recorded_by,
        remarks=remarks,
    )
    attendance_record.full_clean()
    attendance_record.save(
        update_fields=[
            "status",
            "recorded_by",
            "recorded_at",
            "remarks",
            "updated_at",
        ]
    )

    for procedure in performed_procedures:
        procedure_log, _ = ProcedureLog.objects.get_or_create(
            self_practice_session=session,
            student=session.student,
            module_offering=session.module_offering,
            procedure=procedure,
            defaults={
                "performed_count": 1,
            },
        )
        procedure_log.mark_verified(
            verified_by=recorded_by,
            remarks=remarks,
        )
        procedure_log.full_clean()
        procedure_log.save(
            update_fields=[
                "status",
                "verified_by",
                "verified_at",
                "remarks",
                "updated_at",
            ]
        )

    session.status = SessionStatus.COMPLETED
    session.save(update_fields=["status", "updated_at"])

    booking = session.booking
    booking.status = BookingStatus.COMPLETED
    booking.save(update_fields=["status", "updated_at"])

    return session