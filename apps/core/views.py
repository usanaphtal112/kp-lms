from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView, ListView

from apps.accounts.mixins import ITAdminRequiredMixin
from .models import AuditLog
from .navigation import get_dashboard_cards


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("core:dashboard")

        return super().dispatch(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pages/dashboard.html"
    login_url = "account_login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dashboard_cards"] = get_dashboard_cards(self.request.user)
        return context


class AuditLogListView(ITAdminRequiredMixin, ListView):
    model = AuditLog
    template_name = "core/audit_log_list.html"
    context_object_name = "audit_logs"
    paginate_by = 50

    def get_queryset(self):
        queryset = AuditLog.objects.select_related(
            "actor",
            "target_content_type",
        ).order_by("-created_at")

        q = self.request.GET.get("q")
        action = self.request.GET.get("action")
        app_label = self.request.GET.get("app_label")

        if q:
            queryset = queryset.filter(
                object_repr__icontains=q
            ) | queryset.filter(
                message__icontains=q
            ) | queryset.filter(
                actor__username__icontains=q
            )

        if action:
            queryset = queryset.filter(action=action)

        if app_label:
            queryset = queryset.filter(app_label=app_label)

        return queryset