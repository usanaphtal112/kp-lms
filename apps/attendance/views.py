from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView, UpdateView

from apps.accounts.models import UserRole
from apps.academics.models import ModuleOffering
from apps.bookings.models import BookingStatus
from apps.labs.models import DemonstrationSession, SessionStatus

from .forms import AttendanceRecordUpdateForm, AttendanceSessionFilterForm
from .mixins import (
    AttendanceMonitorRequiredMixin,
    AttendanceStaffRequiredMixin,
    ensure_lecturer_owns_session,
)
from .models import AttendanceChangeLog, AttendanceRecord, AttendanceStatus, EligibilitySnapshot
from .services import (
    calculate_student_module_attendance,
    get_attendance_rows_for_session,
    get_student_attendance_summaries,
    record_session_attendance,
    refresh_module_offering_eligibility,
)


class AttendanceDashboardView(AttendanceStaffRequiredMixin, TemplateView):
    template_name = "attendance/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sessions = DemonstrationSession.objects.select_related(
            "booking",
            "lecturer",
            "module_offering",
            "module_offering__module",
        )

        if getattr(self.request.user, "role", None) == UserRole.LECTURER:
            sessions = sessions.filter(lecturer=self.request.user)

        context["scheduled_count"] = sessions.filter(
            status=SessionStatus.SCHEDULED,
            booking__status=BookingStatus.APPROVED,
        ).count()
        context["completed_count"] = sessions.filter(
            status=SessionStatus.COMPLETED,
            booking__status=BookingStatus.COMPLETED,
        ).count()
        context["unmarked_count"] = sessions.filter(
            status=SessionStatus.SCHEDULED,
            booking__status=BookingStatus.APPROVED,
            booking__start_at__lte=timezone.now(),
        ).count()

        context["eligible_count"] = EligibilitySnapshot.objects.filter(
            is_self_practice_eligible=True,
        ).count()

        return context


class AttendanceSessionListView(AttendanceStaffRequiredMixin, ListView):
    model = DemonstrationSession
    template_name = "attendance/session_list.html"
    context_object_name = "sessions"
    paginate_by = 20

    def get_queryset(self):
        queryset = DemonstrationSession.objects.select_related(
            "booking",
            "booking__lab_room",
            "lecturer",
            "module_offering",
            "module_offering__module",
            "module_offering__cohort",
        ).filter(
            booking__status__in=[
                BookingStatus.APPROVED,
                BookingStatus.COMPLETED,
            ]
        )

        if getattr(self.request.user, "role", None) == UserRole.LECTURER:
            queryset = queryset.filter(lecturer=self.request.user)

        form = AttendanceSessionFilterForm(self.request.GET)

        if form.is_valid():
            q = form.cleaned_data.get("q")
            status = form.cleaned_data.get("status")

            if q:
                queryset = queryset.filter(
                    Q(topic__icontains=q)
                    | Q(module_offering__module__code__icontains=q)
                    | Q(module_offering__module__title__icontains=q)
                    | Q(module_offering__cohort__code__icontains=q)
                    | Q(lecturer__first_name__icontains=q)
                    | Q(lecturer__last_name__icontains=q)
                    | Q(lecturer__username__icontains=q)
                )

            if status:
                queryset = queryset.filter(status=status)

        return queryset.order_by("-booking__start_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = AttendanceSessionFilterForm(self.request.GET)
        return context


class AttendanceMarkView(AttendanceStaffRequiredMixin, View):
    template_name = "attendance/mark_session.html"

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            DemonstrationSession.objects.select_related(
                "booking",
                "booking__lab_room",
                "lecturer",
                "module_offering",
                "module_offering__module",
                "module_offering__cohort",
            ),
            pk=kwargs["session_pk"],
        )

        ensure_lecturer_owns_session(request.user, self.session)

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(
            request,
            self.template_name,
            self.get_context_data(),
        )

    def post(self, request, *args, **kwargs):
        rows = get_attendance_rows_for_session(self.session)
        attendance_data = {}

        for row in rows:
            student = row["student"]
            status = request.POST.get(
                f"status_{student.pk}",
                AttendanceStatus.UNMARKED,
            )
            remarks = request.POST.get(
                f"remarks_{student.pk}",
                "",
            )

            attendance_data[student.pk] = {
                "status": status,
                "remarks": remarks,
            }

        mark_completed = request.POST.get("mark_session_completed") == "on"

        result = record_session_attendance(
            session=self.session,
            attendance_data=attendance_data,
            recorded_by=request.user,
            mark_session_completed=mark_completed,
        )

        messages.success(
            request,
            (
                "Attendance saved successfully. "
                f"Created: {result['created_count']}, "
                f"Updated: {result['updated_count']}."
            ),
        )

        return redirect("attendance:session_mark", session_pk=self.session.pk)

    def get_context_data(self):
        return {
            "session": self.session,
            "attendance_rows": get_attendance_rows_for_session(self.session),
            "status_choices": AttendanceStatus.choices,
        }


class ModuleAttendanceSummaryView(AttendanceMonitorRequiredMixin, DetailView):
    model = ModuleOffering
    template_name = "attendance/module_summary.html"
    context_object_name = "offering"
    pk_url_kwarg = "offering_pk"

    def get_queryset(self):
        queryset = ModuleOffering.objects.select_related(
            "module",
            "cohort",
            "academic_year",
            "semester",
            "coordinator",
        )

        if getattr(self.request.user, "role", None) == UserRole.LECTURER:
            queryset = queryset.filter(coordinator=self.request.user)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        enrollments = self.object.enrollments.select_related(
            "student",
            "student__student_profile",
        ).filter(is_active=True)

        context["summaries"] = [
            calculate_student_module_attendance(
                enrollment.student,
                self.object,
            )
            for enrollment in enrollments
        ]

        return context


class RefreshEligibilityView(AttendanceMonitorRequiredMixin, View):
    def post(self, request, offering_pk):
        offering = get_object_or_404(ModuleOffering, pk=offering_pk)

        if getattr(request.user, "role", None) == UserRole.LECTURER:
            if offering.coordinator_id != request.user.id:
                messages.error(request, "You can only refresh your own module offering.")
                return redirect("attendance:dashboard")

        snapshots = refresh_module_offering_eligibility(offering)

        messages.success(
            request,
            f"Eligibility refreshed for {len(snapshots)} students.",
        )

        return redirect("attendance:module_summary", offering_pk=offering.pk)


class EligibilitySnapshotListView(AttendanceMonitorRequiredMixin, ListView):
    model = EligibilitySnapshot
    template_name = "attendance/eligibility_list.html"
    context_object_name = "snapshots"
    paginate_by = 30

    def get_queryset(self):
        queryset = EligibilitySnapshot.objects.select_related(
            "student",
            "student__student_profile",
            "module_offering",
            "module_offering__module",
            "module_offering__cohort",
        )

        if getattr(self.request.user, "role", None) == UserRole.LECTURER:
            queryset = queryset.filter(module_offering__coordinator=self.request.user)

        return queryset.order_by(
            "module_offering__module__code",
            "student__student_profile__registration_number",
        )


class AttendanceRecordUpdateView(AttendanceStaffRequiredMixin, UpdateView):
    model = AttendanceRecord
    form_class = AttendanceRecordUpdateForm
    template_name = "attendance/record_form.html"
    context_object_name = "attendance_record"

    def get_queryset(self):
        queryset = AttendanceRecord.objects.select_related(
            "student",
            "student__student_profile",
            "demonstration_session",
            "demonstration_session__module_offering",
        )

        if getattr(self.request.user, "role", None) == UserRole.LECTURER:
            queryset = queryset.filter(
                demonstration_session__lecturer=self.request.user,
            )

        return queryset

    def form_valid(self, form):
        old_status = self.object.status
        old_remarks = self.object.remarks

        self.object = form.save(commit=False)
        self.object.recorded_by = self.request.user
        self.object.recorded_at = timezone.now()
        self.object.save()

        AttendanceChangeLog.objects.create(
            attendance_record=self.object,
            actor=self.request.user,
            old_status=old_status,
            new_status=self.object.status,
            old_remarks=old_remarks,
            new_remarks=self.object.remarks,
            change_reason=form.cleaned_data.get("change_reason", ""),
        )

        refresh_module_offering_eligibility(
            self.object.demonstration_session.module_offering
        )

        messages.success(self.request, "Attendance record updated successfully.")

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "attendance:session_mark",
            kwargs={
                "session_pk": self.object.demonstration_session_id,
            },
        )


class StudentAttendanceView(LoginRequiredMixin, TemplateView):
    template_name = "attendance/my_attendance.html"
    login_url = "account_login"

    def dispatch(self, request, *args, **kwargs):
        if getattr(request.user, "role", None) != UserRole.STUDENT:
            messages.error(request, "This page is only available to students.")
            return redirect("attendance:dashboard")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summaries"] = get_student_attendance_summaries(self.request.user)
        return context