from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from apps.academics.models import ModuleEnrollmentStatus
from apps.attendance.services import calculate_student_module_attendance
from apps.core.audit import log_audit
from apps.core.models import AuditAction
from apps.notifications.models import NotificationType
from apps.notifications.services import notify_admins

from .models import (
    AttemptStatus,
    AttemptType,
    OSCEAttempt,
    OSCEExamStatus,
    OSCEResult,
    OSCEScore,
    RetakeRequestStatus,
    OSCEMarkAuditLog,
)


def quantize_mark(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def is_student_eligible_for_osce(student, module_offering):
    summary = calculate_student_module_attendance(
        student,
        module_offering,
    )
    return summary["is_osce_eligible"], summary


@transaction.atomic
def generate_osce_attempts_for_eligible_students(*, osce_exam, created_by):
    module_offering = osce_exam.module_offering

    enrollments = module_offering.enrollments.select_related(
        "student",
        "student__student_profile",
    ).filter(
        is_active=True,
        status__in=[
            ModuleEnrollmentStatus.ENROLLED,
            ModuleEnrollmentStatus.IN_PROGRESS,
            ModuleEnrollmentStatus.COMPLETED,
        ],
    )

    created_count = 0
    skipped_count = 0
    ineligible_students = []

    for enrollment in enrollments:
        student = enrollment.student
        eligible, summary = is_student_eligible_for_osce(
            student,
            module_offering,
        )

        if not eligible:
            skipped_count += 1
            ineligible_students.append(
                {
                    "student": student,
                    "attendance_percentage": summary["attendance_percentage"],
                    "required_percentage": summary["required_percentage"],
                }
            )
            continue

        _, created = OSCEAttempt.objects.get_or_create(
            osce_exam=osce_exam,
            student=student,
            attempt_number=1,
            defaults={
                "attempt_type": AttemptType.FIRST_ATTEMPT,
                "status": AttemptStatus.CREATED,
                "created_by": created_by,
            },
        )

        if created:
            created_count += 1
        else:
            skipped_count += 1

    return {
        "created_count": created_count,
        "skipped_count": skipped_count,
        "ineligible_students": ineligible_students,
    }

@transaction.atomic
def save_attempt_scores(*, attempt, score_data, marked_by):
    for rubric_item, score_value in score_data.items():
        station = rubric_item.station

        score, _ = OSCEScore.objects.get_or_create(
            attempt=attempt,
            station=station,
            rubric_item=rubric_item,
            defaults={
                "score": Decimal("0.00"),
            },
        )
        old_score = score.score

        score.score = score_value
        score.marked_by = marked_by
        score.marked_at = timezone.now()
        score.full_clean()
        score.save(
            update_fields=[
                "score",
                "marked_by",
                "marked_at",
                "remarks",
            ]
        )

        if old_score != score_value:
            OSCEMarkAuditLog.objects.create(
                score=score,
                attempt=attempt,
                rubric_item=rubric_item,
                actor=marked_by,
                old_score=old_score,
                new_score=score_value,
                reason="OSCE mark entry or update.",
            )

            log_audit(
                actor=marked_by,
                action=AuditAction.MARK_CHANGE,
                target_object=score,
                message="OSCE score changed.",
                old_values={"score": str(old_score)},
                new_values={"score": str(score_value)},
            )

    attempt.status = AttemptStatus.SUBMITTED
    attempt.submitted_by = marked_by
    attempt.submitted_at = timezone.now()
    attempt.save(
        update_fields=[
            "status",
            "submitted_by",
            "submitted_at",
            "updated_at",
        ]
    )

    return calculate_osce_result(attempt=attempt)


@transaction.atomic
def calculate_osce_result(*, attempt):
    rubric_items = []

    for station in attempt.osce_exam.stations.filter(is_active=True).prefetch_related(
        "rubric_items"
    ):
        rubric_items.extend(list(station.rubric_items.all()))

    total_possible_score = sum(
        item.max_score for item in rubric_items
    ) or Decimal("0.00")

    scores = {
        score.rubric_item_id: score
        for score in attempt.scores.select_related("rubric_item")
    }

    total_score = Decimal("0.00")

    for item in rubric_items:
        score = scores.get(item.id)

        if score:
            total_score += score.score

    if total_possible_score == 0:
        percentage = Decimal("0.00")
    else:
        percentage = (total_score / total_possible_score) * Decimal("100.00")

    percentage = quantize_mark(percentage)
    pass_mark = attempt.osce_exam.module_offering.module.pass_mark
    is_passed = percentage >= pass_mark

    if attempt.attempt_type == AttemptType.RETAKE and is_passed:
        final_mark = Decimal("60.00")
    else:
        final_mark = percentage

    result, _ = OSCEResult.objects.update_or_create(
        attempt=attempt,
        defaults={
            "total_score": quantize_mark(total_score),
            "total_possible_score": quantize_mark(total_possible_score),
            "percentage": percentage,
            "final_mark": quantize_mark(final_mark),
            "pass_mark": pass_mark,
            "is_passed": is_passed,
            "calculated_at": timezone.now(),
        },
    )

    attempt.status = AttemptStatus.CALCULATED
    attempt.save(update_fields=["status", "updated_at"])

    return result


@transaction.atomic
def approve_exam_results(*, osce_exam, approved_by):
    attempts = osce_exam.attempts.select_related("result")

    approved_count = 0

    for attempt in attempts:
        if not hasattr(attempt, "result"):
            calculate_osce_result(attempt=attempt)

        result = attempt.result
        result.approved_by = approved_by
        result.approved_at = timezone.now()
        result.save(update_fields=["approved_by", "approved_at"])

        attempt.status = AttemptStatus.APPROVED
        attempt.save(update_fields=["status", "updated_at"])

        approved_count += 1

    osce_exam.status = OSCEExamStatus.RESULTS_APPROVED
    osce_exam.approved_by = approved_by
    osce_exam.approved_at = timezone.now()
    osce_exam.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at",
            "updated_at",
        ]
    )

    log_audit(
        actor=approved_by,
        action=AuditAction.APPROVE,
        target_object=osce_exam,
        message=f"Approved {approved_count} OSCE results.",
    )

    notify_admins(
        actor=approved_by,
        title="OSCE results approved",
        message=f"Results approved for {osce_exam.title}.",
        notification_type=NotificationType.OSCE,
        url=f"/assessments/exams/{osce_exam.pk}/",
    )

    return approved_count


@transaction.atomic
def publish_exam_results(*, osce_exam, published_by):
    if osce_exam.status != OSCEExamStatus.RESULTS_APPROVED:
        raise ValueError("Only approved OSCE results can be published.")

    now = timezone.now()

    for attempt in osce_exam.attempts.select_related("result"):
        if hasattr(attempt, "result"):
            result = attempt.result
            result.is_published = True
            result.published_at = now
            result.save(update_fields=["is_published", "published_at"])

            attempt.status = AttemptStatus.PUBLISHED
            attempt.save(update_fields=["status", "updated_at"])

    osce_exam.status = OSCEExamStatus.PUBLISHED
    osce_exam.published_by = published_by
    osce_exam.published_at = now
    osce_exam.save(
        update_fields=[
            "status",
            "published_by",
            "published_at",
            "updated_at",
        ]
    )

    log_audit(
        actor=published_by,
        action=AuditAction.PUBLISH,
        target_object=osce_exam,
        message="OSCE results published.",
    )

    return osce_exam


@transaction.atomic
def approve_retake_request(*, retake_request, reviewed_by, comments=""):
    if retake_request.status != RetakeRequestStatus.REQUESTED:
        raise ValueError("Only requested retake requests can be approved.")

    latest_attempt_number = (
        OSCEAttempt.objects.filter(
            osce_exam=retake_request.osce_exam,
            student=retake_request.student,
        )
        .order_by("-attempt_number")
        .values_list("attempt_number", flat=True)
        .first()
        or 1
    )

    retake_attempt = OSCEAttempt.objects.create(
        osce_exam=retake_request.osce_exam,
        student=retake_request.student,
        attempt_number=latest_attempt_number + 1,
        attempt_type=AttemptType.RETAKE,
        status=AttemptStatus.CREATED,
        created_by=reviewed_by,
    )

    retake_request.status = RetakeRequestStatus.APPROVED
    retake_request.reviewed_by = reviewed_by
    retake_request.reviewed_at = timezone.now()
    retake_request.review_comments = comments
    retake_request.created_attempt = retake_attempt
    retake_request.save(
        update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
            "review_comments",
            "created_attempt",
        ]
    )

    return retake_attempt


@transaction.atomic
def reject_retake_request(*, retake_request, reviewed_by, comments=""):
    if retake_request.status != RetakeRequestStatus.REQUESTED:
        raise ValueError("Only requested retake requests can be rejected.")

    retake_request.status = RetakeRequestStatus.REJECTED
    retake_request.reviewed_by = reviewed_by
    retake_request.reviewed_at = timezone.now()
    retake_request.review_comments = comments
    retake_request.save(
        update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
            "review_comments",
        ]
    )

    return retake_request