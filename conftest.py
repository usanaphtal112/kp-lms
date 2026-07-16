from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.accounts.models import StaffProfile, StudentProfile, UserRole
from apps.academics.models import (
    AcademicYear,
    Cohort,
    Department,
    Faculty,
    Module,
    ModuleEnrollment,
    ModuleOffering,
    Procedure,
    Program,
    Semester,
)
from apps.assessments.models import (
    AttemptStatus,
    AttemptType,
    OSCEAttempt,
    OSCEExam,
    OSCERubricItem,
    OSCEScore,
    OSCEStation,
)
from apps.attendance.models import AttendanceRecord, AttendanceStatus
from apps.bookings.models import BookingStatus, BookingType, LabBooking
from apps.inventory.models import (
    InventoryCategory,
    InventoryUsage,
    InventoryUsageItem,
    StockBatch,
    StockItem,
    Supplier,
)
from apps.labs.models import DemonstrationSession, LabRoom, SessionStatus
from apps.reports.models import ClinicalReport


@pytest.fixture
def lecturer_user(db):
    User = get_user_model()

    user = User.objects.create_user(
        username="lecturer1",
        password="testpass123",
        first_name="Lecturer",
        last_name="One",
        email="lecturer1@example.com",
        role=UserRole.LECTURER,
        must_change_password=False,
    )

    StaffProfile.objects.create(
        user=user,
        staff_number="STF001",
        job_title="Lecturer",
        department_name="Nursing",
    )

    return user


@pytest.fixture
def lab_coordinator_user(db):
    User = get_user_model()

    user = User.objects.create_user(
        username="coordinator1",
        password="testpass123",
        first_name="Coordinator",
        last_name="One",
        email="coordinator1@example.com",
        role=UserRole.LAB_COORDINATOR,
        must_change_password=False,
    )

    StaffProfile.objects.create(
        user=user,
        staff_number="STF002",
        job_title="Skills Lab Coordinator",
        department_name="Nursing",
    )

    return user


@pytest.fixture
def faculty(db):
    return Faculty.objects.create(
        name="Faculty of Health Sciences",
        code="FHS",
    )


@pytest.fixture
def department(faculty):
    return Department.objects.create(
        faculty=faculty,
        name="Department of Nursing",
        code="NUR",
    )


@pytest.fixture
def program(department):
    return Program.objects.create(
        department=department,
        name="Bachelor of Nursing Sciences",
        code="BNS",
        award_type="BACHELOR",
        duration_years=4,
    )


@pytest.fixture
def cohort(program):
    return Cohort.objects.create(
        program=program,
        name="BNS Intake 2026",
        code="BNS-2026",
        intake_year=2026,
        graduation_year=2030,
        status="ACTIVE",
    )


@pytest.fixture
def academic_year(db):
    return AcademicYear.objects.create(
        name="2026/2027",
        start_date="2026-09-01",
        end_date="2027-08-31",
        is_current=True,
    )


@pytest.fixture
def semester(academic_year):
    return Semester.objects.create(
        academic_year=academic_year,
        name="Semester I",
        semester_number=1,
        start_date="2026-09-01",
        end_date="2027-01-31",
        is_current=True,
    )


@pytest.fixture
def module(program):
    return Module.objects.create(
        program=program,
        code="FON101",
        title="Fundamentals of Nursing I",
        year_level=1,
        semester_number=1,
        credits=12,
        attendance_requirement=Decimal("80.00"),
        pass_mark=Decimal("60.00"),
    )


@pytest.fixture
def procedure(module):
    return Procedure.objects.create(
        module=module,
        code="PROC001",
        name="Hand Washing",
        minimum_required_practices=1,
        is_required=True,
    )


@pytest.fixture
def module_offering(module, cohort, academic_year, semester, lecturer_user):
    return ModuleOffering.objects.create(
        module=module,
        cohort=cohort,
        academic_year=academic_year,
        semester=semester,
        coordinator=lecturer_user,
        status="ONGOING",
    )


@pytest.fixture
def student(db, program, cohort):
    User = get_user_model()

    user = User.objects.create_user(
        username="2500000124@kplms",
        password="testpass123",
        first_name="Aline",
        last_name="Uwase",
        email="aline@example.com",
        role=UserRole.STUDENT,
        must_change_password=False,
    )

    StudentProfile.objects.create(
        user=user,
        registration_number="2500000124",
        student_type="REGULAR",
        academic_status="ACTIVE",
        current_academic_level=1,
        admission_year=2026,
        program=program,
        cohort=cohort,
        is_active_student=True,
    )

    return user


@pytest.fixture
def module_enrollment(student, module_offering):
    return ModuleEnrollment.objects.create(
        student=student,
        module_offering=module_offering,
        enrollment_type="NORMAL",
        status="ENROLLED",
        is_active=True,
    )


@pytest.fixture
def lab_room(db):
    return LabRoom.objects.create(
        code="LAB001",
        name="Clinical Skills Lab 1",
        location="Health Sciences Block",
        capacity=40,
    )


@pytest.fixture
def completed_demonstration_session_factory(
    module_offering,
    lecturer_user,
    lab_room,
    module_enrollment,
):
    def _factory(**kwargs):
        index = DemonstrationSession.objects.count() + 1
        start_at = kwargs.pop(
            "start_at",
            timezone.now() - timedelta(days=index, hours=2),
        )
        end_at = kwargs.pop(
            "end_at",
            start_at + timedelta(hours=2),
        )

        booking = LabBooking.objects.create(
            booking_type=BookingType.DEMONSTRATION,
            requested_by=lecturer_user,
            module_offering=module_offering,
            lab_room=lab_room,
            title=kwargs.pop("title", f"Demonstration {index}"),
            start_at=start_at,
            end_at=end_at,
            status=BookingStatus.COMPLETED,
        )

        return DemonstrationSession.objects.create(
            booking=booking,
            module_offering=module_offering,
            lecturer=lecturer_user,
            topic=kwargs.pop("topic", f"Demo Topic {index}"),
            description=kwargs.pop("description", ""),
            status=SessionStatus.COMPLETED,
        )

    return _factory


@pytest.fixture
def attendance_record_factory(module_enrollment):
    def _factory(**kwargs):
        return AttendanceRecord.objects.create(
            student=kwargs["student"],
            demonstration_session=kwargs["demonstration_session"],
            status=kwargs.get("status", AttendanceStatus.PRESENT),
            recorded_by=kwargs.get("recorded_by"),
            recorded_at=kwargs.get("recorded_at", timezone.now()),
            remarks=kwargs.get("remarks", ""),
        )

    return _factory


@pytest.fixture
def osce_exam(module_offering, procedure, lecturer_user):
    exam = OSCEExam.objects.create(
        module_offering=module_offering,
        title="FON101 OSCE",
        exam_date=timezone.localdate(),
        status="READY",
        created_by=lecturer_user,
    )

    station = OSCEStation.objects.create(
        osce_exam=exam,
        procedure=procedure,
        title="Hand Washing Station",
        station_order=1,
        duration_minutes=10,
        max_score=Decimal("100.00"),
    )

    OSCERubricItem.objects.create(
        station=station,
        criterion="Performs hand washing correctly",
        max_score=Decimal("100.00"),
        item_order=1,
    )

    return exam


@pytest.fixture
def osce_attempt_factory(student, osce_exam, lecturer_user, module_enrollment):
    def _factory(**kwargs):
        return OSCEAttempt.objects.create(
            osce_exam=kwargs.pop("osce_exam", osce_exam),
            student=kwargs.pop("student", student),
            attempt_number=kwargs.pop("attempt_number", 1),
            attempt_type=kwargs.pop("attempt_type", AttemptType.FIRST_ATTEMPT),
            status=kwargs.pop("status", AttemptStatus.CREATED),
            created_by=kwargs.pop("created_by", lecturer_user),
            remarks=kwargs.pop("remarks", ""),
        )

    return _factory


@pytest.fixture
def osce_score_factory():
    def _factory(**kwargs):
        return OSCEScore.objects.create(
            attempt=kwargs["attempt"],
            station=kwargs["station"],
            rubric_item=kwargs["rubric_item"],
            score=kwargs.get("score", Decimal("0.00")),
            marked_by=kwargs.get("marked_by"),
            marked_at=kwargs.get("marked_at", timezone.now()),
            remarks=kwargs.get("remarks", ""),
        )

    return _factory


@pytest.fixture
def inventory_category(db):
    return InventoryCategory.objects.create(
        code="CON",
        name="Consumables",
    )


@pytest.fixture
def stock_item(inventory_category):
    return StockItem.objects.create(
        category=inventory_category,
        code="GLV001",
        name="Medical Gloves",
        item_type="CONSUMABLE",
        unit="BOX",
        minimum_stock_level=Decimal("10.00"),
        reorder_level=Decimal("20.00"),
    )


@pytest.fixture
def supplier(db):
    return Supplier.objects.create(
        name="ABC Medical Supplies",
        contact_person="Supplier Contact",
        phone_number="0780000000",
        email="supplier@example.com",
    )


@pytest.fixture
def stock_batch_factory(stock_item, supplier):
    def _factory(**kwargs):
        index = StockBatch.objects.count() + 1

        quantity_received = kwargs.pop("quantity_received", Decimal("100.00"))
        quantity_remaining = kwargs.pop("quantity_remaining", quantity_received)

        return StockBatch.objects.create(
            stock_item=kwargs.pop("stock_item", stock_item),
            supplier=kwargs.pop("supplier", supplier),
            batch_number=kwargs.pop("batch_number", f"BATCH-{index:03d}"),
            quantity_received=quantity_received,
            quantity_remaining=quantity_remaining,
            unit_cost=kwargs.pop("unit_cost", Decimal("0.00")),
            received_at=kwargs.pop("received_at", timezone.localdate()),
            expiry_date=kwargs.pop("expiry_date", None),
            status=kwargs.pop("status", "AVAILABLE"),
            notes=kwargs.pop("notes", ""),
        )

    return _factory


@pytest.fixture
def inventory_usage(admin_user):
    return InventoryUsage.objects.create(
        usage_context="GENERAL",
        title="Test inventory usage",
        submitted_by=admin_user,
        status="DRAFT",
    )


@pytest.fixture
def inventory_usage_item_factory(stock_item):
    def _factory(**kwargs):
        quantity_requested = kwargs.pop("quantity_requested", Decimal("1.00"))

        return InventoryUsageItem.objects.create(
            usage=kwargs["usage"],
            stock_item=kwargs.pop("stock_item", stock_item),
            quantity_requested=quantity_requested,
            quantity_approved=kwargs.pop("quantity_approved", Decimal("0.00")),
            remarks=kwargs.pop("remarks", ""),
        )

    return _factory


@pytest.fixture
def clinical_report(student, module_offering, module_enrollment):
    return ClinicalReport.objects.create(
        student=student,
        module_offering=module_offering,
        title="Clinical Report 1",
        facility_name="KP Teaching Hospital",
        department_or_unit="Medical Ward",
        clinical_start_date=timezone.localdate(),
        activities_performed="Observed and practiced basic nursing procedures.",
        skills_practiced="Hand washing, vital signs, patient communication.",
        reflection="Good learning experience.",
        challenges="Limited time.",
        supervisor_name="Clinical Supervisor",
        status="DRAFT",
    )