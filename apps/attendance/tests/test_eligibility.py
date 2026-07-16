from decimal import Decimal

import pytest

from apps.attendance.models import AttendanceStatus
from apps.attendance.services import calculate_student_module_attendance


@pytest.mark.django_db
def test_attendance_eligibility_counts_present_and_late(
    student,
    module_offering,
    completed_demonstration_session_factory,
    attendance_record_factory,
):
    session_1 = completed_demonstration_session_factory(module_offering=module_offering)
    session_2 = completed_demonstration_session_factory(module_offering=module_offering)
    session_3 = completed_demonstration_session_factory(module_offering=module_offering)
    session_4 = completed_demonstration_session_factory(module_offering=module_offering)
    session_5 = completed_demonstration_session_factory(module_offering=module_offering)

    attendance_record_factory(student=student, demonstration_session=session_1, status=AttendanceStatus.PRESENT)
    attendance_record_factory(student=student, demonstration_session=session_2, status=AttendanceStatus.PRESENT)
    attendance_record_factory(student=student, demonstration_session=session_3, status=AttendanceStatus.LATE)
    attendance_record_factory(student=student, demonstration_session=session_4, status=AttendanceStatus.PRESENT)
    attendance_record_factory(student=student, demonstration_session=session_5, status=AttendanceStatus.ABSENT)

    summary = calculate_student_module_attendance(student, module_offering)

    assert summary["attendance_percentage"] == Decimal("80.00")
    assert summary["is_self_practice_eligible"] is True
    assert summary["is_osce_eligible"] is True