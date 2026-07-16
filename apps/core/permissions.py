from django.core.exceptions import PermissionDenied

from apps.accounts.models import UserRole


ADMIN_ROLES = {
    UserRole.IT_ADMIN,
    UserRole.ADMINISTRATION,
}

STAFF_ROLES = {
    UserRole.IT_ADMIN,
    UserRole.ADMINISTRATION,
    UserRole.LECTURER,
    UserRole.LAB_COORDINATOR,
}


def require_authenticated(user):
    if not user or not user.is_authenticated:
        raise PermissionDenied("Authentication required.")


def require_role(user, allowed_roles):
    require_authenticated(user)

    if user.is_superuser:
        return True

    if getattr(user, "role", None) not in allowed_roles:
        raise PermissionDenied("You do not have permission to access this resource.")

    return True


def is_admin_user(user):
    return bool(
        user
        and user.is_authenticated
        and (
            user.is_superuser
            or getattr(user, "role", None) in ADMIN_ROLES
        )
    )


def can_manage_accounts(user):
    return is_admin_user(user) or getattr(user, "role", None) == UserRole.IT_ADMIN


def can_review_clinical_report(user, report):
    if is_admin_user(user):
        return True

    return (
        getattr(user, "role", None) == UserRole.LECTURER
        and report.module_offering.coordinator_id == user.id
    )


def can_view_student_object(user, student):
    if is_admin_user(user):
        return True

    if getattr(user, "role", None) == UserRole.STUDENT:
        return user.id == student.id

    return False


def can_mark_osce_attempt(user, attempt):
    if is_admin_user(user):
        return True

    return (
        getattr(user, "role", None) == UserRole.LECTURER
        and attempt.osce_exam.module_offering.coordinator_id == user.id
    )


def can_download_clinical_report(user, report):
    if can_view_student_object(user, report.student):
        return True

    return can_review_clinical_report(user, report)


def can_approve_inventory(user):
    return is_admin_user(user) or getattr(user, "role", None) == UserRole.LAB_COORDINATOR