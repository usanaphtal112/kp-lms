from django.urls import path

from .views import (
    BookingApproveView,
    BookingDashboardView,
    BookingDetailView,
    BookingRejectView,
    DemonstrationBookingCreateView,
    DemonstrationBookingListView,
)


app_name = "bookings"

urlpatterns = [
    path("", BookingDashboardView.as_view(), name="dashboard"),
    path("demonstrations/", DemonstrationBookingListView.as_view(), name="demonstration_list"),
    path("demonstrations/create/", DemonstrationBookingCreateView.as_view(), name="demonstration_create"),
    path("<int:pk>/", BookingDetailView.as_view(), name="booking_detail"),
    path("<int:pk>/approve/", BookingApproveView.as_view(), name="booking_approve"),
    path("<int:pk>/reject/", BookingRejectView.as_view(), name="booking_reject"),
]