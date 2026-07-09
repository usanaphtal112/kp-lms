from django.urls import path

from .views import (
    LabDashboardView,
    LabRoomCreateView,
    LabRoomListView,
    LabRoomUpdateView,
    LabScheduleView,
)


app_name = "labs"

urlpatterns = [
    path("", LabDashboardView.as_view(), name="dashboard"),
    path("rooms/", LabRoomListView.as_view(), name="labroom_list"),
    path("rooms/create/", LabRoomCreateView.as_view(), name="labroom_create"),
    path("rooms/<int:pk>/update/", LabRoomUpdateView.as_view(), name="labroom_update"),
    path("schedule/", LabScheduleView.as_view(), name="schedule"),
]