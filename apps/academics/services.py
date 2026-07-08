from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import (
    AcademicYear,
    CreditTransfer,
    CreditTransferStatus,
    ModuleEnrollment,
    ModuleEnrollmentStatus,
    ModuleOffering,
    ProcedureRequirement,
)


@transaction.atomic
def set_current_academic_year(academic_year):
    AcademicYear.objects.exclude(pk=academic_year.pk).update(is_current=False)
    academic_year.is_current = True
    academic_year.save(update_fields=["is_current", "updated_at"])

    return academic_year


@transaction.atomic
def set_current_semester(semester):
    semester.__class__.objects.exclude(pk=semester.pk).update(is_current=False)
    semester.is_current = True
    semester.save(update_fields=["is_current", "updated_at"])

    if not semester.academic_year.is_current:
        set_current_academic_year(semester.academic_year)

    return semester


@transaction.atomic
def assign_student_to_program_and_cohort(*, student, program, cohort):
    profile = student.student_profile

    if cohort.program_id != program.id:
        raise ValueError("Cohort does not belong to the selected program.")

    profile.program = program
    profile.cohort = cohort
    profile.current_academic_level = 1
    profile.save(
        update_fields=[
            "program",
            "cohort",
            "current_academic_level",
            "updated_at",
        ]
    )

    return profile


@transaction.atomic
def create_missing_procedure_requirements(module_offering):
    created_requirements = []

    procedures = module_offering.module.procedures.filter(
        is_active=True,
        is_required=True,
    )

    for procedure in procedures:
        requirement, created = ProcedureRequirement.objects.get_or_create(
            module_offering=module_offering,
            procedure=procedure,
            defaults={
                "required_count": procedure.minimum_required_practices,
                "is_mandatory": True,
            },
        )

        if created:
            created_requirements.append(requirement)

    return created_requirements


@transaction.atomic
def enroll_student_in_module_offering(
    *,
    student,
    module_offering,
    enrollment_type,
):
    if getattr(student, "role", None) != "STUDENT":
        raise ValueError("Only student users can be enrolled.")

    enrollment, created = ModuleEnrollment.objects.get_or_create(
        student=student,
        module_offering=module_offering,
        defaults={
            "enrollment_type": enrollment_type,
            "status": ModuleEnrollmentStatus.ENROLLED,
        },
    )

    return enrollment, created


@transaction.atomic
def enroll_cohort_students(module_offering):
    User = get_user_model()

    students = User.objects.filter(
        role="STUDENT",
        is_active=True,
        student_profile__cohort=module_offering.cohort,
        student_profile__is_active_student=True,
    ).select_related("student_profile")

    created_count = 0
    existing_count = 0

    for student in students:
        _, created = ModuleEnrollment.objects.get_or_create(
            student=student,
            module_offering=module_offering,
            defaults={
                "status": ModuleEnrollmentStatus.ENROLLED,
            },
        )

        if created:
            created_count += 1
        else:
            existing_count += 1

    return {
        "created_count": created_count,
        "existing_count": existing_count,
    }


@transaction.atomic
def approve_credit_transfer(*, credit_transfer, approved_by, remarks=""):
    credit_transfer.status = CreditTransferStatus.APPROVED
    credit_transfer.approved_by = approved_by
    credit_transfer.approved_at = timezone.now()

    if remarks:
        credit_transfer.remarks = remarks

    credit_transfer.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at",
            "remarks",
            "updated_at",
        ]
    )

    return credit_transfer


@transaction.atomic
def reject_credit_transfer(*, credit_transfer, approved_by, remarks=""):
    credit_transfer.status = CreditTransferStatus.REJECTED
    credit_transfer.approved_by = approved_by
    credit_transfer.approved_at = timezone.now()

    if remarks:
        credit_transfer.remarks = remarks

    credit_transfer.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at",
            "remarks",
            "updated_at",
        ]
    )

    return credit_transfer