from django.urls import path

from .views import (
    ApproveOSCEResultsView,
    ApproveRetakeRequestView,
    GenerateEligibleCandidatesView,
    OSCEAttemptListView,
    OSCEDashboardView,
    OSCEExcelExportView,
    OSCEExamCreateView,
    OSCEExamDetailView,
    OSCEExamListView,
    OSCEExamUpdateView,
    OSCEMarkEntryView,
    OSCERubricItemCreateView,
    OSCERubricItemUpdateView,
    OSCEStationCreateView,
    OSCEStationUpdateView,
    PublishOSCEResultsView,
    RejectRetakeRequestView,
    RetakeRequestCreateView,
    RetakeRequestListView,
    StudentOSCEResultListView,
)


app_name = "assessments"

urlpatterns = [
    path("", OSCEDashboardView.as_view(), name="dashboard"),

    path("exams/", OSCEExamListView.as_view(), name="exam_list"),
    path("exams/create/", OSCEExamCreateView.as_view(), name="exam_create"),
    path("exams/<int:pk>/", OSCEExamDetailView.as_view(), name="exam_detail"),
    path("exams/<int:pk>/update/", OSCEExamUpdateView.as_view(), name="exam_update"),
    path(
        "exams/<int:pk>/generate-candidates/",
        GenerateEligibleCandidatesView.as_view(),
        name="exam_generate_candidates",
    ),
    path(
        "exams/<int:pk>/approve-results/",
        ApproveOSCEResultsView.as_view(),
        name="exam_approve_results",
    ),
    path(
        "exams/<int:pk>/publish-results/",
        PublishOSCEResultsView.as_view(),
        name="exam_publish_results",
    ),
    path(
        "exams/<int:pk>/export-excel/",
        OSCEExcelExportView.as_view(),
        name="exam_export_excel",
    ),

    path(
        "exams/<int:exam_pk>/stations/create/",
        OSCEStationCreateView.as_view(),
        name="station_create",
    ),
    path(
        "stations/<int:pk>/update/",
        OSCEStationUpdateView.as_view(),
        name="station_update",
    ),
    path(
        "stations/<int:station_pk>/rubrics/create/",
        OSCERubricItemCreateView.as_view(),
        name="rubric_create",
    ),
    path(
        "rubrics/<int:pk>/update/",
        OSCERubricItemUpdateView.as_view(),
        name="rubric_update",
    ),

    path("attempts/", OSCEAttemptListView.as_view(), name="attempt_list"),
    path(
        "exams/<int:exam_pk>/attempts/",
        OSCEAttemptListView.as_view(),
        name="attempt_list_by_exam",
    ),
    path(
        "attempts/<int:attempt_pk>/mark/",
        OSCEMarkEntryView.as_view(),
        name="mark_entry",
    ),

    path("my-results/", StudentOSCEResultListView.as_view(), name="my_results"),
    path(
        "attempts/<int:attempt_pk>/request-retake/",
        RetakeRequestCreateView.as_view(),
        name="retake_request_create",
    ),

    path(
        "retake-requests/",
        RetakeRequestListView.as_view(),
        name="retake_request_list",
    ),
    path(
        "retake-requests/<int:pk>/approve/",
        ApproveRetakeRequestView.as_view(),
        name="retake_request_approve",
    ),
    path(
        "retake-requests/<int:pk>/reject/",
        RejectRetakeRequestView.as_view(),
        name="retake_request_reject",
    ),
]