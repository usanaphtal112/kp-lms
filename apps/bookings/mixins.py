from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import UserRole


class BookingRequesterRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.IT_ADMIN,
        UserRole.LECTURER,
        UserRole.LAB_COORDINATOR,
        UserRole.ADMINISTRATION,
    ]


class BookingApproverRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.IT_ADMIN,
        UserRole.LAB_COORDINATOR,
        UserRole.ADMINISTRATION,
    ]