from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import UserRole


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles = []
    login_url = "account_login"
    raise_exception = True

    def test_func(self):
        user = self.request.user

        if not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return getattr(user, "role", None) in self.allowed_roles


class ITAdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = [UserRole.IT_ADMIN]
    