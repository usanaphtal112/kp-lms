from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, FormView, ListView, TemplateView

from .forms import BookingRejectForm, DemonstrationBookingForm
from .mixins import BookingApproverRequiredMixin, BookingRequesterRequiredMixin
from .models import BookingStatus, BookingType, LabBooking
from .services import approve_booking, create_demonstration_booking, reject_booking


class BookingDashboardView(BookingRequesterRequiredMixin, TemplateView):
    template_name = "bookings/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = LabBooking.objects.all()

        if getattr(self.request.user, "role", None) == "LECTURER":
            queryset = queryset.filter(requested_by=self.request.user)

        context["requested_count"] = queryset.filter(
            status=BookingStatus.REQUESTED
        ).count()
        context["approved_count"] = queryset.filter(
            status=BookingStatus.APPROVED
        ).count()
        context["rejected_count"] = queryset.filter(
            status=BookingStatus.REJECTED
        ).count()

        return context


class DemonstrationBookingListView(BookingRequesterRequiredMixin, ListView):
    model = LabBooking
    template_name = "bookings/booking_list.html"
    context_object_name = "bookings"
    paginate_by = 20

    def get_queryset(self):
        queryset = LabBooking.objects.select_related(
            "requested_by",
            "lab_room",
            "module_offering",
            "module_offering__module",
        ).filter(
            booking_type=BookingType.DEMONSTRATION,
        )

        if getattr(self.request.user, "role", None) == "LECTURER":
            queryset = queryset.filter(requested_by=self.request.user)

        return queryset.order_by("-start_at")


class DemonstrationBookingCreateView(BookingRequesterRequiredMixin, FormView):
    template_name = "bookings/demonstration_form.html"
    form_class = DemonstrationBookingForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            booking = create_demonstration_booking(
                requested_by=self.request.user,
                module_offering=form.cleaned_data["module_offering"],
                lab_room=form.cleaned_data["lab_room"],
                title=form.cleaned_data["title"],
                topic=form.cleaned_data["topic"],
                start_at=form.cleaned_data["start_at"],
                end_at=form.cleaned_data["end_at"],
                procedures=form.cleaned_data["procedures"],
                description=form.cleaned_data["description"],
                notes=form.cleaned_data["notes"],
            )
        except Exception as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(
            self.request,
            "Demonstration booking requested successfully.",
        )

        return redirect("bookings:booking_detail", pk=booking.pk)


class BookingDetailView(BookingRequesterRequiredMixin, DetailView):
    model = LabBooking
    template_name = "bookings/booking_detail.html"
    context_object_name = "booking"

    def get_queryset(self):
        queryset = LabBooking.objects.select_related(
            "requested_by",
            "approved_by",
            "lab_room",
            "module_offering",
            "module_offering__module",
        ).prefetch_related(
            "decision_logs",
        )

        if getattr(self.request.user, "role", None) == "LECTURER":
            queryset = queryset.filter(requested_by=self.request.user)

        return queryset


class BookingApproveView(BookingApproverRequiredMixin, FormView):
    def post(self, request, pk):
        booking = get_object_or_404(LabBooking, pk=pk)

        try:
            approve_booking(
                booking=booking,
                approved_by=request.user,
            )
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect("bookings:booking_detail", pk=booking.pk)

        messages.success(request, "Booking approved successfully.")

        return redirect("bookings:booking_detail", pk=booking.pk)


class BookingRejectView(BookingApproverRequiredMixin, FormView):
    template_name = "bookings/reject_form.html"
    form_class = BookingRejectForm

    def dispatch(self, request, *args, **kwargs):
        self.booking = get_object_or_404(LabBooking, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            reject_booking(
                booking=self.booking,
                rejected_by=self.request.user,
                reason=form.cleaned_data["reason"],
            )
        except Exception as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(self.request, "Booking rejected.")

        return redirect("bookings:booking_detail", pk=self.booking.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["booking"] = self.booking
        return context