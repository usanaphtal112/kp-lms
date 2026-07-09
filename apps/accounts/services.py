from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction

from .models import (
    AccountAction,
    AccountActionLog,
    StaffProfile,
    StudentProfile,
    UserRole,
)


ROLE_GROUP_NAMES = {
    UserRole.IT_ADMIN: "IT Administrators",
    UserRole.LECTURER: "Lecturers",
    UserRole.LAB_COORDINATOR: "Skills Lab Coordinators",
    UserRole.ADMINISTRATION: "Administration",
    UserRole.STUDENT: "Students",
}


def normalize_registration_number(registration_number: str) -> str:
    return registration_number.strip().replace(" ", "").upper()


def build_student_username(registration_number: str) -> str:
    normalized_registration_number = normalize_registration_number(registration_number)
    return f"{normalized_registration_number}@kplms".lower()


def get_managed_role_groups():
    return Group.objects.filter(name__in=ROLE_GROUP_NAMES.values())


def assign_user_group(user):
    group_name = ROLE_GROUP_NAMES[user.role]
    group, _ = Group.objects.get_or_create(name=group_name)

    user.groups.remove(*get_managed_role_groups())
    user.groups.add(group)

    return group


def log_account_action(actor, target_user, action, message="", metadata=None):
    return AccountActionLog.objects.create(
        actor=actor,
        target_user=target_user,
        action=action,
        message=message,
        metadata=metadata or {},
    )


@transaction.atomic
def create_student_account(
    *,
    registration_number,
    first_name,
    last_name,
    email="",
    phone_number="",
    student_type,
    academic_status,
    current_academic_level,
    admission_year=None,
    program=None,
    cohort=None,
    created_by=None,
):
    User = get_user_model()

    normalized_registration_number = normalize_registration_number(registration_number)
    username = build_student_username(normalized_registration_number)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=settings.KPLMS_DEFAULT_STUDENT_PASSWORD,
        first_name=first_name,
        last_name=last_name,
        role=UserRole.STUDENT,
        phone_number=phone_number,
        must_change_password=True,
        is_staff=False,
    )

    StudentProfile.objects.create(
        user=user,
        registration_number=normalized_registration_number,
        student_type=student_type,
        academic_status=academic_status,
        current_academic_level=current_academic_level,
        admission_year=admission_year,
        program=program,
        cohort=cohort,
    )

    assign_user_group(user)

    log_account_action(
        actor=created_by,
        target_user=user,
        action=AccountAction.CREATED,
        message="Student account created.",
        metadata={
            "username": username,
            "registration_number": normalized_registration_number,
        },
    )

    return user


@transaction.atomic
def create_staff_account(
    *,
    username,
    first_name,
    last_name,
    email="",
    phone_number="",
    role,
    staff_number=None,
    job_title="",
    department_name="",
    office_location="",
    initial_password=None,
    created_by=None,
):
    if role == UserRole.STUDENT:
        raise ValueError("Use create_student_account() for student accounts.")

    User = get_user_model()

    user = User.objects.create_user(
        username=username.strip().lower(),
        email=email,
        password=initial_password or settings.KPLMS_DEFAULT_STAFF_PASSWORD,
        first_name=first_name,
        last_name=last_name,
        role=role,
        phone_number=phone_number,
        must_change_password=True,
        is_staff=role == UserRole.IT_ADMIN,
    )

    StaffProfile.objects.create(
        user=user,
        staff_number=staff_number or None,
        job_title=job_title,
        department_name=department_name,
        office_location=office_location,
    )

    assign_user_group(user)

    log_account_action(
        actor=created_by,
        target_user=user,
        action=AccountAction.CREATED,
        message="Staff account created.",
        metadata={
            "username": username,
            "role": role,
        },
    )

    return user


@transaction.atomic
def reset_user_password(*, target_user, new_password, reset_by):
    target_user.set_password(new_password)
    target_user.must_change_password = True
    target_user.save(update_fields=["password", "must_change_password"])

    log_account_action(
        actor=reset_by,
        target_user=target_user,
        action=AccountAction.PASSWORD_RESET,
        message="Password reset by IT Administrator.",
    )

    return target_user


@transaction.atomic
def set_user_active_status(*, target_user, is_active, changed_by):
    target_user.is_active = is_active
    target_user.save(update_fields=["is_active"])

    action = AccountAction.ACTIVATED if is_active else AccountAction.DEACTIVATED

    log_account_action(
        actor=changed_by,
        target_user=target_user,
        action=action,
        message=f"User account {'activated' if is_active else 'deactivated'}.",
    )

    return target_user