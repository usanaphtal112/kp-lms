from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import UserRole


class ReportStaffRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.IT_ADMIN,
        UserRole.LECTURER,
        UserRole.ADMINISTRATION,
        UserRole.LAB_COORDINATOR,
    ]


class ReportReviewerRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.IT_ADMIN,
        UserRole.LECTURER,
        UserRole.ADMINISTRATION,
    ]


class AdministrationReportRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.IT_ADMIN,
        UserRole.ADMINISTRATION,
    ]


class StudentRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.STUDENT,
    ]