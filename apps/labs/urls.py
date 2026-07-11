from django.urls import path

from .views import (
    LabDashboardView,
    LabRoomCreateView,
    LabRoomListView,
    LabRoomUpdateView,
    LabScheduleView,
    ProcedureLogListView,
    SelfPracticeApproveView,
    SelfPracticeCreateView,
    SelfPracticeDetailView,
    SelfPracticeListView,
    SelfPracticeOutcomeView,
    SelfPracticeRejectView,
)


app_name = "labs"

urlpatterns = [
    path("", LabDashboardView.as_view(), name="dashboard"),
    path("rooms/", LabRoomListView.as_view(), name="labroom_list"),
    path("rooms/create/", LabRoomCreateView.as_view(), name="labroom_create"),
    path("rooms/<int:pk>/update/", LabRoomUpdateView.as_view(), name="labroom_update"),
    path("schedule/", LabScheduleView.as_view(), name="schedule"),

    path("self-practice/", SelfPracticeListView.as_view(), name="self_practice_list"),
    path("self-practice/create/", SelfPracticeCreateView.as_view(), name="self_practice_create"),
    path("self-practice/<int:pk>/", SelfPracticeDetailView.as_view(), name="self_practice_detail"),
    path("self-practice/<int:pk>/approve/", SelfPracticeApproveView.as_view(), name="self_practice_approve"),
    path("self-practice/<int:pk>/reject/", SelfPracticeRejectView.as_view(), name="self_practice_reject"),
    path("self-practice/<int:pk>/record-outcome/", SelfPracticeOutcomeView.as_view(), name="self_practice_outcome"),

    path("procedure-logs/", ProcedureLogListView.as_view(), name="procedure_log_list"),
]
