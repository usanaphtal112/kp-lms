from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone

from apps.assessments.models import OSCEResult
from apps.attendance.models import EligibilitySnapshot
from apps.labs.models import ProcedureLog, SelfPracticeSession

from .models import (
    ClinicalReport,
    ClinicalTeachingReport,
    PortfolioItem,
    PortfolioItemType,
    ReportReview,
    ReportReviewDecision,
    ReportStatus,
)


@transaction.atomic
def submit_clinical_report(*, report):
    if report.status not in [
        ReportStatus.DRAFT,
        ReportStatus.REVISION_REQUESTED,
    ]:
        raise ValueError("Only draft or revision-requested reports can be submitted.")

    report.status = ReportStatus.SUBMITTED
    report.submitted_at = timezone.now()
    report.save(
        update_fields=[
            "status",
            "submitted_at",
            "updated_at",
        ]
    )

    return report


@transaction.atomic
def submit_clinical_teaching_report(*, report):
    if report.status not in [
        ReportStatus.DRAFT,
        ReportStatus.REVISION_REQUESTED,
    ]:
        raise ValueError("Only draft or revision-requested reports can be submitted.")

    report.status = ReportStatus.SUBMITTED
    report.submitted_at = timezone.now()
    report.save(
        update_fields=[
            "status",
            "submitted_at",
            "updated_at",
        ]
    )

    return report


@transaction.atomic
def review_clinical_report(*, report, reviewer, decision, comments=""):
    if report.status not in [
        ReportStatus.SUBMITTED,
        ReportStatus.UNDER_REVIEW,
    ]:
        raise ValueError("Only submitted reports can be reviewed.")

    report.status = decision
    report.reviewed_by = reviewer
    report.reviewed_at = timezone.now()
    report.review_comments = comments
    report.save(
        update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
            "review_comments",
            "updated_at",
        ]
    )

    ReportReview.objects.create(
        clinical_report=report,
        reviewer=reviewer,
        decision=decision,
        comments=comments,
    )

    if decision == ReportReviewDecision.APPROVED:
        create_portfolio_item_from_clinical_report(
            report=report,
            created_by=reviewer,
        )

    return report


@transaction.atomic
def review_clinical_teaching_report(*, report, reviewer, decision, comments=""):
    if report.status not in [
        ReportStatus.SUBMITTED,
        ReportStatus.UNDER_REVIEW,
    ]:
        raise ValueError("Only submitted teaching reports can be reviewed.")

    report.status = decision
    report.reviewed_by = reviewer
    report.reviewed_at = timezone.now()
    report.review_comments = comments
    report.save(
        update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
            "review_comments",
            "updated_at",
        ]
    )

    ReportReview.objects.create(
        clinical_teaching_report=report,
        reviewer=reviewer,
        decision=decision,
        comments=comments,
    )

    return report


def create_portfolio_item_from_clinical_report(*, report, created_by):
    content_type = ContentType.objects.get_for_model(report)

    portfolio_item, _ = PortfolioItem.objects.get_or_create(
        student=report.student,
        item_type=PortfolioItemType.CLINICAL_REPORT,
        source_content_type=content_type,
        source_object_id=report.pk,
        defaults={
            "module_offering": report.module_offering,
            "title": report.title,
            "description": (
                f"Approved clinical report from {report.facility_name}."
            ),
            "created_by": created_by,
            "is_visible_to_student": True,
        },
    )

    return portfolio_item


def get_student_portfolio_summary(student):
    attendance_snapshots = EligibilitySnapshot.objects.select_related(
        "module_offering",
        "module_offering__module",
    ).filter(
        student=student,
    )

    self_practice_sessions = SelfPracticeSession.objects.select_related(
        "module_offering",
        "module_offering__module",
        "booking",
    ).filter(
        student=student,
    )

    procedure_logs = ProcedureLog.objects.select_related(
        "module_offering",
        "module_offering__module",
        "procedure",
        "verified_by",
    ).filter(
        student=student,
    )

    osce_results = OSCEResult.objects.select_related(
        "attempt",
        "attempt__osce_exam",
        "attempt__osce_exam__module_offering",
        "attempt__osce_exam__module_offering__module",
    ).filter(
        attempt__student=student,
        is_published=True,
    )

    clinical_reports = ClinicalReport.objects.select_related(
        "module_offering",
        "module_offering__module",
        "reviewed_by",
    ).filter(
        student=student,
    )

    manual_items = PortfolioItem.objects.select_related(
        "module_offering",
        "module_offering__module",
    ).filter(
        student=student,
        is_visible_to_student=True,
    )

    return {
        "attendance_snapshots": attendance_snapshots,
        "self_practice_sessions": self_practice_sessions,
        "procedure_logs": procedure_logs,
        "osce_results": osce_results,
        "clinical_reports": clinical_reports,
        "manual_items": manual_items,
    }