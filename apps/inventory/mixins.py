from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import UserRole


class InventoryViewerRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.IT_ADMIN,
        UserRole.LECTURER,
        UserRole.LAB_COORDINATOR,
        UserRole.ADMINISTRATION,
    ]


class InventoryManagerRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.IT_ADMIN,
        UserRole.LAB_COORDINATOR,
        UserRole.ADMINISTRATION,
    ]


class InventorySubmitterRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.IT_ADMIN,
        UserRole.LECTURER,
        UserRole.LAB_COORDINATOR,
        UserRole.ADMINISTRATION,
    ]


class InventoryApproverRequiredMixin(RoleRequiredMixin):
    allowed_roles = [
        UserRole.IT_ADMIN,
        UserRole.LAB_COORDINATOR,
        UserRole.ADMINISTRATION,
    ]