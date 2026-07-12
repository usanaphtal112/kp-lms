from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from apps.accounts.models import UserRole

from .exports import export_osce_results_workbook
from .forms import (
    OSCEExamForm,
    OSCEMarkEntryForm,
    OSCERubricItemForm,
    OSCEStationForm,
    RetakeRequestForm,
    RetakeReviewForm,
)
from .mixins import OSCEApproverRequiredMixin, OSCEStaffRequiredMixin, StudentRequiredMixin
from .models import (
    AttemptStatus,
    OSCEAttempt,
    OSCEExam,
    OSCEResult,
    OSCERubricItem,
    OSCEStation,
    RetakeRequest,
    RetakeRequestStatus,
)
from .services import (
    approve_exam_results,
    approve_retake_request,
    generate_osce_attempts_for_eligible_students,
    publish_exam_results,
    reject_retake_request,
    save_attempt_scores,
)


class OSCEDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "assessments/dashboard.html"
    login_url = "account_login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = getattr(self.request.user, "role", None)

        exams = OSCEExam.objects.all()

        if role == UserRole.LECTURER:
            exams = exams.filter(module_offering__coordinator=self.request.user)
        elif role == UserRole.STUDENT:
            attempts = OSCEAttempt.objects.filter(student=self.request.user)
            context["my_attempt_count"] = attempts.count()
            context["my_published_result_count"] = OSCEResult.objects.filter(
                attempt__student=self.request.user,
                is_published=True,
            ).count()
            return context

        context["exam_count"] = exams.count()
        context["attempt_count"] = OSCEAttempt.objects.filter(
            osce_exam__in=exams
        ).count()
        context["pending_retake_count"] = RetakeRequest.objects.filter(
            status=RetakeRequestStatus.REQUESTED
        ).count()

        return context


class OSCEExamListView(OSCEStaffRequiredMixin, ListView):
    model = OSCEExam
    template_name = "assessments/exam_list.html"
    context_object_name = "exams"
    paginate_by = 20

    def get_queryset(self):
        queryset = OSCEExam.objects.select_related(
            "module_offering",
            "module_offering__module",
            "module_offering__cohort",
            "created_by",
        )

        if getattr(self.request.user, "role", None) == UserRole.LECTURER:
            queryset = queryset.filter(module_offering__coordinator=self.request.user)

        return queryset.order_by("-exam_date")


class OSCEExamCreateView(OSCEStaffRequiredMixin, CreateView):
    model = OSCEExam
    form_class = OSCEExamForm
    template_name = "assessments/exam_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "OSCE exam created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("assessments:exam_detail", kwargs={"pk": self.object.pk})


class OSCEExamUpdateView(OSCEStaffRequiredMixin, UpdateView):
    model = OSCEExam
    form_class = OSCEExamForm
    template_name = "assessments/exam_form.html"

    def get_queryset(self):
        queryset = OSCEExam.objects.all()

        if getattr(self.request.user, "role", None) == UserRole.LECTURER:
            queryset = queryset.filter(module_offering__coordinator=self.request.user)

        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "OSCE exam updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("assessments:exam_detail", kwargs={"pk": self.object.pk})


class OSCEExamDetailView(OSCEStaffRequiredMixin, DetailView):
    model = OSCEExam
    template_name = "assessments/exam_detail.html"
    context_object_name = "exam"

    def get_queryset(self):
        queryset = OSCEExam.objects.select_related(
            "module_offering",
            "module_offering__module",
            "module_offering__cohort",
            "created_by",
            "approved_by",
            "published_by",
        ).prefetch_related(
            "stations__rubric_items",
            "attempts__student",
            "attempts__result",
        )

        if getattr(self.request.user, "role", None) == UserRole.LECTURER:
            queryset = queryset.filter(module_offering__coordinator=self.request.user)

        return queryset


class GenerateEligibleCandidatesView(OSCEStaffRequiredMixin, View):
    def post(self, request, pk):
        exam = get_object_or_404(OSCEExam, pk=pk)

        if getattr(request.user, "role", None) == UserRole.LECTURER:
            if exam.module_offering.coordinator_id != request.user.id:
                messages.error(request, "You can only manage your assigned module exams.")
                return redirect("assessments:exam_list")

        result = generate_osce_attempts_for_eligible_students(
            osce_exam=exam,
            created_by=request.user,
        )

        messages.success(
            request,
            (
                f"Candidate generation complete. "
                f"Created: {result['created_count']}, "
                f"Skipped: {result['skipped_count']}."
            ),
        )

        return redirect("assessments:exam_detail", pk=exam.pk)


class OSCEStationCreateView(OSCEStaffRequiredMixin, CreateView):
    model = OSCEStation
    form_class = OSCEStationForm
    template_name = "assessments/station_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.exam = get_object_or_404(OSCEExam, pk=kwargs["exam_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["osce_exam"] = self.exam
        return kwargs

    def form_valid(self, form):
        form.instance.osce_exam = self.exam
        messages.success(self.request, "OSCE station created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("assessments:exam_detail", kwargs={"pk": self.exam.pk})


class OSCEStationUpdateView(OSCEStaffRequiredMixin, UpdateView):
    model = OSCEStation
    form_class = OSCEStationForm
    template_name = "assessments/station_form.html"

    def get_success_url(self):
        return reverse_lazy(
            "assessments:exam_detail",
            kwargs={"pk": self.object.osce_exam_id},
        )


class OSCERubricItemCreateView(OSCEStaffRequiredMixin, CreateView):
    model = OSCERubricItem
    form_class = OSCERubricItemForm
    template_name = "assessments/rubric_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.station = get_object_or_404(OSCEStation, pk=kwargs["station_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["station"] = self.station
        return kwargs

    def form_valid(self, form):
        form.instance.station = self.station
        messages.success(self.request, "Rubric item created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "assessments:exam_detail",
            kwargs={"pk": self.station.osce_exam_id},
        )


class OSCERubricItemUpdateView(OSCEStaffRequiredMixin, UpdateView):
    model = OSCERubricItem
    form_class = OSCERubricItemForm
    template_name = "assessments/rubric_form.html"

    def get_success_url(self):
        return reverse_lazy(
            "assessments:exam_detail",
            kwargs={"pk": self.object.station.osce_exam_id},
        )


class OSCEAttemptListView(OSCEStaffRequiredMixin, ListView):
    model = OSCEAttempt
    template_name = "assessments/attempt_list.html"
    context_object_name = "attempts"
    paginate_by = 30

    def get_queryset(self):
        queryset = OSCEAttempt.objects.select_related(
            "osce_exam",
            "osce_exam__module_offering",
            "osce_exam__module_offering__module",
            "student",
            "student__student_profile",
            "result",
        )

        if getattr(self.request.user, "role", None) == UserRole.LECTURER:
            queryset = queryset.filter(
                osce_exam__module_offering__coordinator=self.request.user
            )

        exam_pk = self.kwargs.get("exam_pk")

        if exam_pk:
            queryset = queryset.filter(osce_exam_id=exam_pk)

        return queryset.order_by(
            "osce_exam",
            "student__student_profile__registration_number",
        )


class OSCEMarkEntryView(OSCEStaffRequiredMixin, FormView):
    template_name = "assessments/mark_entry.html"
    form_class = OSCEMarkEntryForm

    def dispatch(self, request, *args, **kwargs):
        self.attempt = get_object_or_404(
            OSCEAttempt.objects.select_related(
                "osce_exam",
                "osce_exam__module_offering",
                "osce_exam__module_offering__module",
                "student",
                "student__student_profile",
            ).prefetch_related("scores"),
            pk=kwargs["attempt_pk"],
        )

        if getattr(request.user, "role", None) == UserRole.LECTURER:
            if self.attempt.osce_exam.module_offering.coordinator_id != request.user.id:
                messages.error(request, "You can only mark your assigned module exams.")
                return redirect("assessments:attempt_list")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["attempt"] = self.attempt
        return kwargs

    def form_valid(self, form):
        result = save_attempt_scores(
            attempt=self.attempt,
            score_data=form.get_score_data(),
            marked_by=self.request.user,
        )

        messages.success(
            self.request,
            f"Scores saved. Calculated percentage: {result.percentage}%.",
        )

        return redirect("assessments:attempt_list_by_exam", exam_pk=self.attempt.osce_exam_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["attempt"] = self.attempt
        return context


class ApproveOSCEResultsView(OSCEApproverRequiredMixin, View):
    def post(self, request, pk):
        exam = get_object_or_404(OSCEExam, pk=pk)
        approved_count = approve_exam_results(
            osce_exam=exam,
            approved_by=request.user,
        )

        messages.success(
            request,
            f"Approved {approved_count} OSCE results.",
        )

        return redirect("assessments:exam_detail", pk=exam.pk)


class PublishOSCEResultsView(OSCEApproverRequiredMixin, View):
    def post(self, request, pk):
        exam = get_object_or_404(OSCEExam, pk=pk)

        try:
            publish_exam_results(
                osce_exam=exam,
                published_by=request.user,
            )
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect("assessments:exam_detail", pk=exam.pk)

        messages.success(request, "OSCE results published successfully.")

        return redirect("assessments:exam_detail", pk=exam.pk)


class OSCEExcelExportView(OSCEStaffRequiredMixin, View):
    def get(self, request, pk):
        exam = get_object_or_404(OSCEExam, pk=pk)

        if getattr(request.user, "role", None) == UserRole.LECTURER:
            if exam.module_offering.coordinator_id != request.user.id:
                messages.error(request, "You can only export your assigned module exams.")
                return redirect("assessments:exam_list")

        return export_osce_results_workbook(exam)


class StudentOSCEResultListView(StudentRequiredMixin, ListView):
    model = OSCEResult
    template_name = "assessments/my_results.html"
    context_object_name = "results"

    def get_queryset(self):
        return OSCEResult.objects.select_related(
            "attempt",
            "attempt__osce_exam",
            "attempt__osce_exam__module_offering",
            "attempt__osce_exam__module_offering__module",
        ).filter(
            attempt__student=self.request.user,
            is_published=True,
        ).order_by("-attempt__osce_exam__exam_date")


class RetakeRequestCreateView(StudentRequiredMixin, CreateView):
    model = RetakeRequest
    form_class = RetakeRequestForm
    template_name = "assessments/retake_request_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.attempt = get_object_or_404(
            OSCEAttempt.objects.select_related(
                "osce_exam",
                "result",
            ),
            pk=kwargs["attempt_pk"],
            student=request.user,
        )

        if not hasattr(self.attempt, "result") or self.attempt.result.is_passed:
            messages.error(request, "Retake request is only available for failed attempts.")
            return redirect("assessments:my_results")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.student = self.request.user
        form.instance.osce_exam = self.attempt.osce_exam
        form.instance.original_attempt = self.attempt

        messages.success(self.request, "Retake request submitted successfully.")

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("assessments:my_results")


class RetakeRequestListView(OSCEApproverRequiredMixin, ListView):
    model = RetakeRequest
    template_name = "assessments/retake_request_list.html"
    context_object_name = "retake_requests"
    paginate_by = 30

    def get_queryset(self):
        return RetakeRequest.objects.select_related(
            "student",
            "student__student_profile",
            "osce_exam",
            "original_attempt",
            "reviewed_by",
            "created_attempt",
        ).order_by("-created_at")


class ApproveRetakeRequestView(OSCEApproverRequiredMixin, FormView):
    template_name = "assessments/retake_review_form.html"
    form_class = RetakeReviewForm

    def dispatch(self, request, *args, **kwargs):
        self.retake_request = get_object_or_404(RetakeRequest, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        approve_retake_request(
            retake_request=self.retake_request,
            reviewed_by=self.request.user,
            comments=form.cleaned_data["comments"],
        )

        messages.success(self.request, "Retake request approved.")

        return redirect("assessments:retake_request_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["retake_request"] = self.retake_request
        context["action_label"] = "Approve retake"
        return context


class RejectRetakeRequestView(OSCEApproverRequiredMixin, FormView):
    template_name = "assessments/retake_review_form.html"
    form_class = RetakeReviewForm

    def dispatch(self, request, *args, **kwargs):
        self.retake_request = get_object_or_404(RetakeRequest, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        reject_retake_request(
            retake_request=self.retake_request,
            reviewed_by=self.request.user,
            comments=form.cleaned_data["comments"],
        )

        messages.success(self.request, "Retake request rejected.")

        return redirect("assessments:retake_request_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["retake_request"] = self.retake_request
        context["action_label"] = "Reject retake"
        return context