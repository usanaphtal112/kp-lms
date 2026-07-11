from django.core.exceptions import PermissionDenied

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import UserRole


class AttendanceStaffRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.IT_ADMIN,
        UserRole.LECTURER,
        UserRole.LAB_COORDINATOR,
        UserRole.ADMINISTRATION,
    ]


class AttendanceMonitorRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.IT_ADMIN,
        UserRole.LECTURER,
        UserRole.LAB_COORDINATOR,
        UserRole.ADMINISTRATION,
    ]


def ensure_lecturer_owns_session(user, session):
    if user.is_superuser:
        return

    if getattr(user, "role", None) == UserRole.LECTURER:
        if session.lecturer_id != user.id:
            raise PermissionDenied("You can only manage your own demonstration sessions.")