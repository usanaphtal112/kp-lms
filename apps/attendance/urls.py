from django.urls import path

from .views import (
    AttendanceDashboardView,
    AttendanceMarkView,
    AttendanceRecordUpdateView,
    AttendanceSessionListView,
    EligibilitySnapshotListView,
    ModuleAttendanceSummaryView,
    RefreshEligibilityView,
    StudentAttendanceView,
)


app_name = "attendance"

urlpatterns = [
    path("", AttendanceDashboardView.as_view(), name="dashboard"),
    path("sessions/", AttendanceSessionListView.as_view(), name="session_list"),
    path(
        "sessions/<int:session_pk>/mark/",
        AttendanceMarkView.as_view(),
        name="session_mark",
    ),
    path(
        "module-offerings/<int:offering_pk>/summary/",
        ModuleAttendanceSummaryView.as_view(),
        name="module_summary",
    ),
    path(
        "module-offerings/<int:offering_pk>/refresh-eligibility/",
        RefreshEligibilityView.as_view(),
        name="refresh_eligibility",
    ),
    path(
        "eligibility/",
        EligibilitySnapshotListView.as_view(),
        name="eligibility_list",
    ),
    path(
        "records/<int:pk>/update/",
        AttendanceRecordUpdateView.as_view(),
        name="record_update",
    ),
    path(
        "my-attendance/",
        StudentAttendanceView.as_view(),
        name="my_attendance",
    ),
]