from decimal import Decimal

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.academics.models import Module, Procedure, Program
from apps.accounts.models import (
    StaffProfile,
    StudentAcademicStatus,
    StudentProfile,
    StudentType,
    UserRole,
    YearLevel,
)
from apps.accounts.services import (
    build_student_username,
    create_staff_account,
    create_student_account,
)
from apps.labs.models import LabRoom, DemonstrationSession
from apps.attendance.models import AttendanceRecord, AttendanceStatus
from apps.attendance.services import refresh_module_offering_eligibility


def get_value(row, key, default=""):
    value = row.get(key, default)

    if value is None:
        return default

    return str(value).strip()


def get_int(row, key, default=None):
    value = get_value(row, key)

    if value == "":
        return default

    return int(float(value))


def get_decimal(row, key, default=None):
    value = get_value(row, key)

    if value == "":
        return default

    return Decimal(value)


def get_bool(row, key, default=False):
    value = get_value(row, key).lower()

    if value == "":
        return default

    return value in {"1", "yes", "true", "y", "active"}


class BaseImporter:
    required_columns = set()

    def __init__(self, actor):
        self.actor = actor

    def validate_required_columns(self, row):
        errors = []

        for column in sorted(self.required_columns):
            if get_value(row, column) == "":
                errors.append(f"Missing required column value: {column}")

        return errors

    def validate_row(self, row):
        return self.validate_required_columns(row)

    def import_row(self, row):
        raise NotImplementedError


class StudentImporter(BaseImporter):
    required_columns = {
        "registration_number",
        "first_name",
        "last_name",
        "student_type",
        "academic_status",
        "current_academic_level",
        "program_code",
        "cohort_code",
    }

    def validate_row(self, row):
        errors = super().validate_row(row)

        registration_number = get_value(row, "registration_number")
        username = build_student_username(registration_number)

        User = get_user_model()

        if registration_number and StudentProfile.objects.filter(
            registration_number=registration_number.upper()
        ).exists():
            errors.append("Student profile already exists for this registration number.")

        if username and User.objects.filter(username=username).exists():
            errors.append("User account already exists for this registration number.")

        if get_value(row, "student_type") not in StudentType.values:
            errors.append("Invalid student_type.")

        if get_value(row, "academic_status") not in StudentAcademicStatus.values:
            errors.append("Invalid academic_status.")

        try:
            year_level = get_int(row, "current_academic_level")
            if year_level not in YearLevel.values:
                errors.append("Invalid current_academic_level.")
        except ValueError:
            errors.append("current_academic_level must be a number.")

        program_code = get_value(row, "program_code")
        cohort_code = get_value(row, "cohort_code")

        program = Program.objects.filter(code=program_code).first()

        if not program:
            errors.append("program_code does not exist.")

        if program and not program.cohorts.filter(code=cohort_code).exists():
            errors.append("cohort_code does not exist under the selected program.")

        return errors

    @transaction.atomic
    def import_row(self, row):
        program = Program.objects.get(code=get_value(row, "program_code"))
        cohort = program.cohorts.get(code=get_value(row, "cohort_code"))

        return create_student_account(
            registration_number=get_value(row, "registration_number"),
            first_name=get_value(row, "first_name"),
            last_name=get_value(row, "last_name"),
            email=get_value(row, "email"),
            phone_number=get_value(row, "phone_number"),
            student_type=get_value(row, "student_type"),
            academic_status=get_value(row, "academic_status"),
            current_academic_level=get_int(row, "current_academic_level"),
            admission_year=get_int(row, "admission_year"),
            program=program,
            cohort=cohort,
            created_by=self.actor,
        )


class StaffImporter(BaseImporter):
    required_columns = {
        "username",
        "first_name",
        "last_name",
        "role",
    }

    def validate_row(self, row):
        errors = super().validate_row(row)

        User = get_user_model()

        username = get_value(row, "username").lower()
        role = get_value(row, "role")
        staff_number = get_value(row, "staff_number")

        if username and User.objects.filter(username=username).exists():
            errors.append("Username already exists.")

        if role not in UserRole.values:
            errors.append("Invalid role.")

        if role == UserRole.STUDENT:
            errors.append("Use the student importer for student accounts.")

        if staff_number and StaffProfile.objects.filter(staff_number=staff_number).exists():
            errors.append("Staff number already exists.")

        return errors

    @transaction.atomic
    def import_row(self, row):
        return create_staff_account(
            username=get_value(row, "username").lower(),
            first_name=get_value(row, "first_name"),
            last_name=get_value(row, "last_name"),
            email=get_value(row, "email"),
            phone_number=get_value(row, "phone_number"),
            role=get_value(row, "role"),
            staff_number=get_value(row, "staff_number") or None,
            job_title=get_value(row, "job_title"),
            department_name=get_value(row, "department_name"),
            office_location=get_value(row, "office_location"),
            created_by=self.actor,
        )


class ModuleImporter(BaseImporter):
    required_columns = {
        "program_code",
        "code",
        "title",
        "year_level",
        "semester_number",
    }

    def validate_row(self, row):
        errors = super().validate_row(row)

        program_code = get_value(row, "program_code")
        module_code = get_value(row, "code")

        program = Program.objects.filter(code=program_code).first()

        if not program:
            errors.append("program_code does not exist.")

        if program and Module.objects.filter(program=program, code=module_code).exists():
            errors.append("Module already exists under this program.")

        return errors

    @transaction.atomic
    def import_row(self, row):
        program = Program.objects.get(code=get_value(row, "program_code"))

        return Module.objects.create(
            program=program,
            code=get_value(row, "code").upper(),
            title=get_value(row, "title"),
            year_level=get_int(row, "year_level"),
            semester_number=get_int(row, "semester_number"),
            credits=get_int(row, "credits", default=0) or 0,
            attendance_requirement=get_decimal(
                row,
                "attendance_requirement",
                default=Decimal("80.00"),
            ),
            pass_mark=get_decimal(
                row,
                "pass_mark",
                default=Decimal("60.00"),
            ),
            description=get_value(row, "description"),
        )


class ProcedureImporter(BaseImporter):
    required_columns = {
        "program_code",
        "module_code",
        "code",
        "name",
    }

    def validate_row(self, row):
        errors = super().validate_row(row)

        module = Module.objects.filter(
            program__code=get_value(row, "program_code"),
            code=get_value(row, "module_code"),
        ).first()

        if not module:
            errors.append("Module does not exist for program_code and module_code.")

        if module and Procedure.objects.filter(
            module=module,
            code=get_value(row, "code"),
        ).exists():
            errors.append("Procedure code already exists under this module.")

        return errors

    @transaction.atomic
    def import_row(self, row):
        module = Module.objects.get(
            program__code=get_value(row, "program_code"),
            code=get_value(row, "module_code"),
        )

        return Procedure.objects.create(
            module=module,
            code=get_value(row, "code").upper(),
            name=get_value(row, "name"),
            description=get_value(row, "description"),
            minimum_required_practices=get_int(
                row,
                "minimum_required_practices",
                default=1,
            ) or 1,
            is_required=get_bool(row, "is_required", default=True),
        )


class LabRoomImporter(BaseImporter):
    required_columns = {
        "code",
        "name",
    }

    def validate_row(self, row):
        errors = super().validate_row(row)

        code = get_value(row, "code").upper()

        if code and LabRoom.objects.filter(code=code).exists():
            errors.append("Lab room code already exists.")

        return errors

    @transaction.atomic
    def import_row(self, row):
        return LabRoom.objects.create(
            code=get_value(row, "code").upper(),
            name=get_value(row, "name"),
            location=get_value(row, "location"),
            capacity=get_int(row, "capacity", default=0) or 0,
        )
    
class AttendanceImporter(BaseImporter):
    required_columns = {
        "demonstration_session_id",
        "registration_number",
        "status",
    }

    def validate_row(self, row):
        errors = super().validate_row(row)

        session_id = get_value(row, "demonstration_session_id")
        registration_number = get_value(row, "registration_number").upper()
        status = get_value(row, "status").upper()

        session = DemonstrationSession.objects.filter(pk=session_id).first()

        if not session:
            errors.append("demonstration_session_id does not exist.")

        if status not in AttendanceStatus.values:
            errors.append("Invalid attendance status.")

        profile = StudentProfile.objects.filter(
            registration_number=registration_number
        ).select_related("user").first()

        if not profile:
            errors.append("registration_number does not exist.")

        if session and profile:
            enrolled = profile.user.module_enrollments.filter(
                module_offering=session.module_offering,
                is_active=True,
            ).exists()

            if not enrolled:
                errors.append(
                    "Student is not enrolled in this demonstration's module offering."
                )

        return errors

    @transaction.atomic
    def import_row(self, row):
        session = DemonstrationSession.objects.select_related(
            "module_offering"
        ).get(
            pk=get_value(row, "demonstration_session_id")
        )

        profile = StudentProfile.objects.select_related("user").get(
            registration_number=get_value(row, "registration_number").upper()
        )

        record, _ = AttendanceRecord.objects.update_or_create(
            student=profile.user,
            demonstration_session=session,
            defaults={
                "status": get_value(row, "status").upper(),
                "remarks": get_value(row, "remarks"),
                "recorded_by": self.actor,
                "recorded_at": timezone.now(),
            },
        )

        refresh_module_offering_eligibility(session.module_offering)

        return record


IMPORTER_REGISTRY = {
    "STUDENTS": StudentImporter,
    "STAFF": StaffImporter,
    "MODULES": ModuleImporter,
    "PROCEDURES": ProcedureImporter,
    "LAB_ROOMS": LabRoomImporter,
    "ATTENDANCE": AttendanceImporter,
}


def get_importer(importer_type, actor):
    importer_class = IMPORTER_REGISTRY[importer_type]
    return importer_class(actor=actor)