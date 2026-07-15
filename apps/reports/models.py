from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class ReportStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    REVISION_REQUESTED = "REVISION_REQUESTED", "Revision Requested"


class ReportReviewDecision(models.TextChoices):
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    REVISION_REQUESTED = "REVISION_REQUESTED", "Revision Requested"


class ClinicalReport(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clinical_reports",
        limit_choices_to={"role": "STUDENT"},
    )
    module_offering = models.ForeignKey(
        "academics.ModuleOffering",
        on_delete=models.PROTECT,
        related_name="clinical_reports",
    )

    title = models.CharField(max_length=180)
    facility_name = models.CharField(max_length=180)
    department_or_unit = models.CharField(max_length=180, blank=True)
    clinical_start_date = models.DateField()
    clinical_end_date = models.DateField(null=True, blank=True)

    activities_performed = models.TextField()
    skills_practiced = models.TextField(blank=True)
    reflection = models.TextField(blank=True)
    challenges = models.TextField(blank=True)
    supervisor_name = models.CharField(max_length=180, blank=True)

    attachment = models.FileField(
        upload_to="clinical-reports/%Y/%m/",
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=40,
        choices=ReportStatus.choices,
        default=ReportStatus.DRAFT,
        db_index=True,
    )

    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_clinical_reports",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["clinical_start_date"]),
        ]

    def clean(self):
        super().clean()

        if self.student_id and getattr(self.student, "role", None) != "STUDENT":
            raise ValidationError("Only student users can submit clinical reports.")

        if self.student_id and self.module_offering_id:
            enrolled = self.student.module_enrollments.filter(
                module_offering=self.module_offering,
                is_active=True,
            ).exists()

            if not enrolled:
                raise ValidationError(
                    "Student must be enrolled in the selected module offering."
                )

        if self.clinical_end_date and self.clinical_start_date:
            if self.clinical_end_date < self.clinical_start_date:
                raise ValidationError(
                    "Clinical end date cannot be before start date."
                )

    def __str__(self):
        return f"{self.student} - {self.title}"


class ClinicalTeachingReport(models.Model):
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clinical_teaching_reports",
        limit_choices_to={"role": "LECTURER"},
    )
    module_offering = models.ForeignKey(
        "academics.ModuleOffering",
        on_delete=models.PROTECT,
        related_name="clinical_teaching_reports",
    )

    title = models.CharField(max_length=180)
    facility_name = models.CharField(max_length=180)
    department_or_unit = models.CharField(max_length=180, blank=True)
    teaching_date = models.DateField()
    topic_taught = models.CharField(max_length=180)
    students_supervised_count = models.PositiveIntegerField(default=0)

    objectives = models.TextField(blank=True)
    teaching_activities = models.TextField()
    observations = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)

    attachment = models.FileField(
        upload_to="clinical-teaching-reports/%Y/%m/",
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=40,
        choices=ReportStatus.choices,
        default=ReportStatus.DRAFT,
        db_index=True,
    )

    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_clinical_teaching_reports",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-teaching_date", "-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["teaching_date"]),
        ]

    def clean(self):
        super().clean()

        if self.lecturer_id and getattr(self.lecturer, "role", None) != "LECTURER":
            raise ValidationError(
                "Only lecturers can submit clinical teaching reports."
            )

    def __str__(self):
        return f"{self.lecturer} - {self.title}"


class ReportReview(models.Model):
    clinical_report = models.ForeignKey(
        ClinicalReport,
        on_delete=models.CASCADE,
        related_name="reviews",
        null=True,
        blank=True,
    )
    clinical_teaching_report = models.ForeignKey(
        ClinicalTeachingReport,
        on_delete=models.CASCADE,
        related_name="reviews",
        null=True,
        blank=True,
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="report_reviews",
        null=True,
        blank=True,
    )
    decision = models.CharField(
        max_length=40,
        choices=ReportReviewDecision.choices,
    )
    comments = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-reviewed_at"]

    def clean(self):
        super().clean()

        selected_reports = [
            self.clinical_report_id,
            self.clinical_teaching_report_id,
        ]

        if sum(1 for value in selected_reports if value) != 1:
            raise ValidationError(
                "A review must be linked to exactly one report."
            )

    def __str__(self):
        return f"{self.reviewer} - {self.decision}"


class PortfolioItemType(models.TextChoices):
    ATTENDANCE = "ATTENDANCE", "Attendance"
    SELF_PRACTICE = "SELF_PRACTICE", "Self-practice"
    PROCEDURE_LOG = "PROCEDURE_LOG", "Procedure Log"
    OSCE_RESULT = "OSCE_RESULT", "OSCE Result"
    CLINICAL_REPORT = "CLINICAL_REPORT", "Clinical Report"
    CREDIT_TRANSFER = "CREDIT_TRANSFER", "Credit Transfer"
    MANUAL_EVIDENCE = "MANUAL_EVIDENCE", "Manual Evidence"
    OTHER = "OTHER", "Other"


class PortfolioItem(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="portfolio_items",
        limit_choices_to={"role": "STUDENT"},
    )
    module_offering = models.ForeignKey(
        "academics.ModuleOffering",
        on_delete=models.SET_NULL,
        related_name="portfolio_items",
        null=True,
        blank=True,
    )

    item_type = models.CharField(
        max_length=40,
        choices=PortfolioItemType.choices,
        default=PortfolioItemType.MANUAL_EVIDENCE,
    )
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    evidence_file = models.FileField(
        upload_to="portfolio-evidence/%Y/%m/",
        null=True,
        blank=True,
    )

    source_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    source_object_id = models.PositiveBigIntegerField(null=True, blank=True)
    source_object = GenericForeignKey(
        "source_content_type",
        "source_object_id",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_portfolio_items",
        null=True,
        blank=True,
    )
    is_visible_to_student = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["item_type"]),
            models.Index(fields=["created_at"]),
        ]

    def clean(self):
        super().clean()

        if self.student_id and getattr(self.student, "role", None) != "STUDENT":
            raise ValidationError("Portfolio items can only belong to students.")

    def __str__(self):
        return f"{self.student} - {self.title}"