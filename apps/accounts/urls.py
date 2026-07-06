from django.urls import path

from .views import (
    AccountDashboardView,
    AdminPasswordResetView,
    StaffAccountCreateView,
    StudentAccountCreateView,
    UserActivateView,
    UserDeactivateView,
    UserDetailView,
    UserListView,
    UserUpdateView,
)


app_name = "accounts"

urlpatterns = [
    path("", AccountDashboardView.as_view(), name="dashboard"),
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user_detail"),
    path("users/<int:pk>/update/", UserUpdateView.as_view(), name="user_update"),
    path(
        "users/<int:pk>/reset-password/",
        AdminPasswordResetView.as_view(),
        name="admin_password_reset",
    ),
    path(
        "users/<int:pk>/activate/",
        UserActivateView.as_view(),
        name="user_activate",
    ),
    path(
        "users/<int:pk>/deactivate/",
        UserDeactivateView.as_view(),
        name="user_deactivate",
    ),
    path(
        "students/create/",
        StudentAccountCreateView.as_view(),
        name="student_create",
    ),
    path(
        "staff/create/",
        StaffAccountCreateView.as_view(),
        name="staff_create",
    ),
]