from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import UserRole


class BulkImportManagerRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.IT_ADMIN,
        UserRole.ADMINISTRATION,
    ]