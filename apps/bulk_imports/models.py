from django.conf import settings
from django.db import models


class ImporterType(models.TextChoices):
    STUDENTS = "STUDENTS", "Students"
    STAFF = "STAFF", "Staff / Lecturers"
    MODULES = "MODULES", "Modules"
    PROCEDURES = "PROCEDURES", "Procedures"
    LAB_ROOMS = "LAB_ROOMS", "Lab rooms"


class ImportBatchStatus(models.TextChoices):
    UPLOADED = "UPLOADED", "Uploaded"
    VALIDATED = "VALIDATED", "Validated"
    PARTIALLY_IMPORTED = "PARTIALLY_IMPORTED", "Partially imported"
    IMPORTED = "IMPORTED", "Imported"
    FAILED = "FAILED", "Failed"


class ImportRowStatus(models.TextChoices):
    VALID = "VALID", "Valid"
    INVALID = "INVALID", "Invalid"
    IMPORTED = "IMPORTED", "Imported"
    FAILED = "FAILED", "Failed"


class ImportBatch(models.Model):
    importer_type = models.CharField(
        max_length=40,
        choices=ImporterType.choices,
    )
    file = models.FileField(upload_to="imports/%Y/%m/")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_import_batches",
    )
    status = models.CharField(
        max_length=40,
        choices=ImportBatchStatus.choices,
        default=ImportBatchStatus.UPLOADED,
    )

    total_rows = models.PositiveIntegerField(default=0)
    valid_rows = models.PositiveIntegerField(default=0)
    invalid_rows = models.PositiveIntegerField(default=0)
    imported_rows = models.PositiveIntegerField(default=0)
    failed_rows = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    committed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_importer_type_display()} import #{self.pk}"


class ImportRow(models.Model):
    batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.CASCADE,
        related_name="rows",
    )
    row_number = models.PositiveIntegerField()
    raw_data = models.JSONField(default=dict)
    errors = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=30,
        choices=ImportRowStatus.choices,
    )
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["row_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["batch", "row_number"],
                name="unique_row_number_per_import_batch",
            ),
        ]

    def __str__(self):
        return f"{self.batch} row {self.row_number}"