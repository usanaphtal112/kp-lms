from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import UserRole


class OSCEStaffRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.IT_ADMIN,
        UserRole.LECTURER,
        UserRole.ADMINISTRATION,
    ]


class OSCEApproverRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.IT_ADMIN,
        UserRole.ADMINISTRATION,
    ]


class StudentRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.STUDENT,
    ]