from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView, DetailView, FormView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from apps.bookings.models import BookingStatus, LabBooking
from apps.accounts.models import UserRole
from apps.bookings.models import BookingStatus
from apps.attendance.services import calculate_student_module_attendance
from .forms import LabRoomForm
from .mixins import LabManagerRequiredMixin

from .forms import (
    LabRoomForm,
    SelfPracticeApprovalForm,
    SelfPracticeBookingForm,
    SelfPracticeOutcomeForm,
    SelfPracticeRejectForm,
)
from .mixins import (
    LabManagerRequiredMixin,
    SelfPracticeApproverRequiredMixin,
    SelfPracticeStaffRequiredMixin,
    StudentRequiredMixin,
)
from .models import LabRoom, ProcedureLog, SelfPracticeSession
from .services import (
    approve_self_practice_session,
    create_self_practice_booking,
    record_self_practice_outcome,
    reject_self_practice_session,
)


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
    
class SelfPracticeListView(LoginRequiredMixin, ListView):
    model = SelfPracticeSession
    template_name = "labs/self_practice_list.html"
    context_object_name = "sessions"
    paginate_by = 20
    login_url = "account_login"

    def get_queryset(self):
        queryset = SelfPracticeSession.objects.select_related(
            "booking",
            "booking__lab_room",
            "student",
            "student__student_profile",
            "supervisor",
            "module_offering",
            "module_offering__module",
            "module_offering__cohort",
        ).prefetch_related("planned_procedures__procedure")

        role = getattr(self.request.user, "role", None)

        if role == UserRole.STUDENT:
            queryset = queryset.filter(student=self.request.user)
        elif role == UserRole.LECTURER:
            queryset = queryset.filter(supervisor=self.request.user)
        elif role not in [
            UserRole.IT_ADMIN,
            UserRole.LAB_COORDINATOR,
            UserRole.ADMINISTRATION,
        ]:
            queryset = queryset.none()

        return queryset.order_by("-booking__start_at")


class SelfPracticeCreateView(StudentRequiredMixin, FormView):
    template_name = "labs/self_practice_form.html"
    form_class = SelfPracticeBookingForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["student"] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            session = create_self_practice_booking(
                student=self.request.user,
                module_offering=form.cleaned_data["module_offering"],
                lab_room=form.cleaned_data["lab_room"],
                start_at=form.cleaned_data["start_at"],
                end_at=form.cleaned_data["end_at"],
                procedures=form.cleaned_data["procedures"],
                objectives=form.cleaned_data["objectives"],
                notes=form.cleaned_data["notes"],
            )
        except Exception as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(
            self.request,
            "Self-practice request submitted successfully.",
        )

        return redirect("labs:self_practice_detail", pk=session.pk)


class SelfPracticeDetailView(LoginRequiredMixin, DetailView):
    model = SelfPracticeSession
    template_name = "labs/self_practice_detail.html"
    context_object_name = "session"
    login_url = "account_login"

    def get_queryset(self):
        queryset = SelfPracticeSession.objects.select_related(
            "booking",
            "booking__lab_room",
            "booking__approved_by",
            "student",
            "student__student_profile",
            "supervisor",
            "module_offering",
            "module_offering__module",
            "module_offering__cohort",
        ).prefetch_related(
            "planned_procedures__procedure",
            "procedure_logs__procedure",
        )

        role = getattr(self.request.user, "role", None)

        if role == UserRole.STUDENT:
            queryset = queryset.filter(student=self.request.user)
        elif role == UserRole.LECTURER:
            queryset = queryset.filter(supervisor=self.request.user)
        elif role not in [
            UserRole.IT_ADMIN,
            UserRole.LAB_COORDINATOR,
            UserRole.ADMINISTRATION,
        ]:
            queryset = queryset.none()

        return queryset


class SelfPracticeApproveView(SelfPracticeApproverRequiredMixin, FormView):
    template_name = "labs/self_practice_approve.html"
    form_class = SelfPracticeApprovalForm

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(SelfPracticeSession, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            approve_self_practice_session(
                session=self.session,
                approved_by=self.request.user,
                supervisor=form.cleaned_data["supervisor"],
                comments=form.cleaned_data["comments"],
            )
        except Exception as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(self.request, "Self-practice request approved.")

        return redirect("labs:self_practice_detail", pk=self.session.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["session"] = self.session
        return context


class SelfPracticeRejectView(SelfPracticeApproverRequiredMixin, FormView):
    template_name = "labs/self_practice_reject.html"
    form_class = SelfPracticeRejectForm

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(SelfPracticeSession, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            reject_self_practice_session(
                session=self.session,
                rejected_by=self.request.user,
                reason=form.cleaned_data["reason"],
            )
        except Exception as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(self.request, "Self-practice request rejected.")

        return redirect("labs:self_practice_detail", pk=self.session.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["session"] = self.session
        return context


class SelfPracticeOutcomeView(SelfPracticeStaffRequiredMixin, FormView):
    template_name = "labs/self_practice_outcome.html"
    form_class = SelfPracticeOutcomeForm

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            SelfPracticeSession.objects.select_related(
                "booking",
                "student",
                "module_offering",
                "module_offering__module",
            ),
            pk=kwargs["pk"],
        )

        role = getattr(request.user, "role", None)

        if role == UserRole.LECTURER and self.session.supervisor_id != request.user.id:
            messages.error(request, "You can only record sessions assigned to you.")
            return redirect("labs:self_practice_list")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["session"] = self.session
        return kwargs

    def form_valid(self, form):
        try:
            record_self_practice_outcome(
                session=self.session,
                recorded_by=self.request.user,
                attendance_status=form.cleaned_data["attendance_status"],
                performed_procedures=form.cleaned_data["performed_procedures"],
                remarks=form.cleaned_data["remarks"],
            )
        except Exception as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(
            self.request,
            "Self-practice attendance and procedure verification saved.",
        )

        return redirect("labs:self_practice_detail", pk=self.session.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["session"] = self.session
        return context


class ProcedureLogListView(LoginRequiredMixin, ListView):
    model = ProcedureLog
    template_name = "labs/procedure_log_list.html"
    context_object_name = "procedure_logs"
    paginate_by = 30
    login_url = "account_login"

    def get_queryset(self):
        queryset = ProcedureLog.objects.select_related(
            "student",
            "student__student_profile",
            "module_offering",
            "module_offering__module",
            "procedure",
            "verified_by",
        )

        role = getattr(self.request.user, "role", None)

        if role == UserRole.STUDENT:
            queryset = queryset.filter(student=self.request.user)
        elif role == UserRole.LECTURER:
            queryset = queryset.filter(verified_by=self.request.user)
        elif role not in [
            UserRole.IT_ADMIN,
            UserRole.LAB_COORDINATOR,
            UserRole.ADMINISTRATION,
        ]:
            queryset = queryset.none()

        return queryset.order_by("-created_at")