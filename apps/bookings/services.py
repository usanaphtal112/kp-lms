from django.db import transaction

from apps.labs.models import DemonstrationProcedure, DemonstrationSession

from .models import (
    BookingDecisionAction,
    BookingDecisionLog,
    BookingStatus,
    BookingType,
    LabBooking,
)


@transaction.atomic
def create_demonstration_booking(
    *,
    requested_by,
    module_offering,
    lab_room,
    title,
    topic,
    start_at,
    end_at,
    procedures,
    description="",
    notes="",
):
    booking = LabBooking(
        booking_type=BookingType.DEMONSTRATION,
        requested_by=requested_by,
        module_offering=module_offering,
        lab_room=lab_room,
        title=title,
        start_at=start_at,
        end_at=end_at,
        notes=notes,
        status=BookingStatus.REQUESTED,
    )
    booking.full_clean()
    booking.save()

    session = DemonstrationSession(
        booking=booking,
        module_offering=module_offering,
        lecturer=requested_by,
        topic=topic,
        description=description,
    )
    session.full_clean()
    session.save()

    for procedure in procedures:
        session_procedure = DemonstrationProcedure(
            demonstration_session=session,
            procedure=procedure,
        )
        session_procedure.full_clean()
        session_procedure.save()

    return booking


@transaction.atomic
def approve_booking(*, booking, approved_by, comments=""):
    if booking.status != BookingStatus.REQUESTED:
        raise ValueError("Only requested bookings can be approved.")

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

    BookingDecisionLog.objects.create(
        booking=booking,
        actor=approved_by,
        action=BookingDecisionAction.APPROVED,
        comments=comments,
    )

    return booking


@transaction.atomic
def reject_booking(*, booking, rejected_by, reason):
    if booking.status != BookingStatus.REQUESTED:
        raise ValueError("Only requested bookings can be rejected.")

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

    return booking