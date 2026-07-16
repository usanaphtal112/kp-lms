from django.urls import path

from .views import (
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationReadView,
)


app_name = "notifications"

urlpatterns = [
    path("", NotificationListView.as_view(), name="list"),
    path("<int:pk>/read/", NotificationReadView.as_view(), name="read"),
    path("mark-all-read/", NotificationMarkAllReadView.as_view(), name="mark_all_read"),
]