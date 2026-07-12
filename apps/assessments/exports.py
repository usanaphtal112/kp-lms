from io import BytesIO

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font


def export_osce_results_workbook(osce_exam):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "OSCE Results"

    headers = [
        "Registration Number",
        "Student Name",
        "Username",
        "Module",
        "Exam",
        "Attempt Number",
        "Attempt Type",
        "Total Score",
        "Total Possible",
        "Percentage",
        "Final Mark",
        "Pass Mark",
        "Passed",
        "Approved",
        "Published",
    ]

    worksheet.append(headers)

    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    attempts = osce_exam.attempts.select_related(
        "student",
        "student__student_profile",
        "result",
    ).order_by(
        "student__student_profile__registration_number",
        "attempt_number",
    )

    for attempt in attempts:
        result = getattr(attempt, "result", None)
        student_profile = getattr(attempt.student, "student_profile", None)

        worksheet.append(
            [
                getattr(student_profile, "registration_number", ""),
                attempt.student.get_full_name(),
                attempt.student.username,
                osce_exam.module_offering.module.code,
                osce_exam.title,
                attempt.attempt_number,
                attempt.get_attempt_type_display(),
                result.total_score if result else "",
                result.total_possible_score if result else "",
                result.percentage if result else "",
                result.final_mark if result else "",
                result.pass_mark if result else "",
                "Yes" if result and result.is_passed else "No",
                "Yes" if result and result.approved_at else "No",
                "Yes" if result and result.is_published else "No",
            ]
        )

    for column_cells in worksheet.columns:
        max_length = 0
        column_letter = column_cells[0].column_letter

        for cell in column_cells:
            value = str(cell.value or "")
            max_length = max(max_length, len(value))

        worksheet.column_dimensions[column_letter].width = min(max_length + 2, 35)

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )
    response["Content-Disposition"] = (
        f'attachment; filename="osce-results-{osce_exam.pk}.xlsx"'
    )

    return response