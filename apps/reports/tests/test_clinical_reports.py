import pytest

from apps.reports.models import ReportStatus
from apps.reports.services import review_clinical_report, submit_clinical_report


@pytest.mark.django_db
def test_approved_clinical_report_creates_portfolio_item(clinical_report, lecturer_user):
    submit_clinical_report(report=clinical_report)

    review_clinical_report(
        report=clinical_report,
        reviewer=lecturer_user,
        decision=ReportStatus.APPROVED,
        comments="Good report.",
    )

    clinical_report.refresh_from_db()

    assert clinical_report.status == ReportStatus.APPROVED
    assert clinical_report.student.portfolio_items.filter(
        title=clinical_report.title,
    ).exists()