from django.contrib.auth.mixins import LoginRequiredMixin

from apps.core.permissions import require_role

from .models import UserRole


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = ()
    login_url = "account_login"

    def dispatch(self, request, *args, **kwargs):
        require_role(request.user, self.allowed_roles)
        return super().dispatch(request, *args, **kwargs)


class ITAdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = [UserRole.IT_ADMIN]
    