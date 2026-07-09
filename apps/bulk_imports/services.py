from django.db import transaction
from django.utils import timezone

from .importers import get_importer
from .models import (
    ImportBatch,
    ImportBatchStatus,
    ImportRow,
    ImportRowStatus,
)
from .parsers import read_tabular_file


def validate_import_file(*, importer_type, uploaded_file, uploaded_by):
    rows = read_tabular_file(uploaded_file)

    uploaded_file.seek(0)

    batch = ImportBatch.objects.create(
        importer_type=importer_type,
        file=uploaded_file,
        uploaded_by=uploaded_by,
        total_rows=len(rows),
    )

    importer = get_importer(importer_type, actor=uploaded_by)

    valid_rows = 0
    invalid_rows = 0

    for index, row in enumerate(rows, start=2):
        errors = importer.validate_row(row)
        status = ImportRowStatus.INVALID if errors else ImportRowStatus.VALID

        if errors:
            invalid_rows += 1
        else:
            valid_rows += 1

        ImportRow.objects.create(
            batch=batch,
            row_number=index,
            raw_data=row,
            errors=errors,
            status=status,
        )

    batch.valid_rows = valid_rows
    batch.invalid_rows = invalid_rows
    batch.status = ImportBatchStatus.VALIDATED
    batch.save(
        update_fields=[
            "valid_rows",
            "invalid_rows",
            "status",
        ]
    )

    return batch


def commit_import_batch(*, batch, actor):
    importer = get_importer(batch.importer_type, actor=actor)

    imported_rows = 0
    failed_rows = 0

    valid_rows = batch.rows.filter(status=ImportRowStatus.VALID)

    for import_row in valid_rows:
        try:
            with transaction.atomic():
                created_object = importer.import_row(import_row.raw_data)

                import_row.status = ImportRowStatus.IMPORTED
                import_row.object_id = str(created_object.pk)
                import_row.object_repr = str(created_object)
                import_row.errors = []
                import_row.save(
                    update_fields=[
                        "status",
                        "object_id",
                        "object_repr",
                        "errors",
                    ]
                )

                imported_rows += 1

        except Exception as exc:
            import_row.status = ImportRowStatus.FAILED
            import_row.errors = [str(exc)]
            import_row.save(update_fields=["status", "errors"])

            failed_rows += 1

    batch.imported_rows = imported_rows
    batch.failed_rows = failed_rows
    batch.committed_at = timezone.now()

    if failed_rows:
        batch.status = ImportBatchStatus.PARTIALLY_IMPORTED
    else:
        batch.status = ImportBatchStatus.IMPORTED

    batch.save(
        update_fields=[
            "imported_rows",
            "failed_rows",
            "committed_at",
            "status",
        ]
    )

    return batch