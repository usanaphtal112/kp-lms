from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import UserRole


class LabManagerRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.IT_ADMIN,
        UserRole.LAB_COORDINATOR,
        UserRole.ADMINISTRATION,
    ]