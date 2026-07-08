from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import UserRole


class AcademicManagerRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.IT_ADMIN,
        UserRole.ADMINISTRATION,
    ]