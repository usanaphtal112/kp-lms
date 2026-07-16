from django.urls import path

from .views import DashboardView, HomeView, AuditLogListView


app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("audit-logs/", AuditLogListView.as_view(), name="audit_log_list"),
]