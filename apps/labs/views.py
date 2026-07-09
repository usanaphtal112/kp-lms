from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from apps.bookings.models import BookingStatus, LabBooking

from .forms import LabRoomForm
from .mixins import LabManagerRequiredMixin
from .models import LabRoom


class LabDashboardView(LabManagerRequiredMixin, TemplateView):
    template_name = "labs/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["room_count"] = LabRoom.objects.count()
        context["active_room_count"] = LabRoom.objects.filter(is_active=True).count()
        context["pending_booking_count"] = LabBooking.objects.filter(
            status=BookingStatus.REQUESTED
        ).count()
        context["approved_booking_count"] = LabBooking.objects.filter(
            status=BookingStatus.APPROVED
        ).count()

        return context


class LabRoomListView(LabManagerRequiredMixin, ListView):
    model = LabRoom
    template_name = "labs/labroom_list.html"
    context_object_name = "lab_rooms"
    paginate_by = 20


class LabRoomCreateView(LabManagerRequiredMixin, CreateView):
    model = LabRoom
    form_class = LabRoomForm
    template_name = "labs/labroom_form.html"
    success_url = reverse_lazy("labs:labroom_list")


class LabRoomUpdateView(LabManagerRequiredMixin, UpdateView):
    model = LabRoom
    form_class = LabRoomForm
    template_name = "labs/labroom_form.html"
    success_url = reverse_lazy("labs:labroom_list")


class LabScheduleView(LabManagerRequiredMixin, ListView):
    model = LabBooking
    template_name = "labs/schedule.html"
    context_object_name = "bookings"
    paginate_by = 30

    def get_queryset(self):
        return LabBooking.objects.select_related(
            "lab_room",
            "module_offering",
            "module_offering__module",
            "requested_by",
        ).filter(
            status__in=[
                BookingStatus.REQUESTED,
                BookingStatus.APPROVED,
            ]
        ).order_by("start_at")