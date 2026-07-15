from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
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

from .exports import (
    export_clinical_reports_workbook,
    export_clinical_teaching_reports_workbook,
    export_student_portfolio_workbook,
)
from .forms import (
    ClinicalReportForm,
    ClinicalTeachingReportForm,
    PortfolioItemForm,
    ReportReviewForm,
)
from .mixins import (
    AdministrationReportRequiredMixin,
    ReportReviewerRequiredMixin,
    ReportStaffRequiredMixin,
    StudentRequiredMixin,
)
from .models import (
    ClinicalReport,
    ClinicalTeachingReport,
    PortfolioItem,
    ReportStatus,
)
from .services import (
    get_student_portfolio_summary,
    review_clinical_report,
    review_clinical_teaching_report,
    submit_clinical_report,
    submit_clinical_teaching_report,
)


class ReportsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "reports/dashboard.html"
    login_url = "account_login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = getattr(self.request.user, "role", None)

        if role == UserRole.STUDENT:
            context["my_clinical_reports_count"] = ClinicalReport.objects.filter(
                student=self.request.user
            ).count()
            context["approved_clinical_reports_count"] = ClinicalReport.objects.filter(
                student=self.request.user,
                status=ReportStatus.APPROVED,
            ).count()
            return context

        if role == UserRole.LECTURER:
            context["my_teaching_reports_count"] = ClinicalTeachingReport.objects.filter(
                lecturer=self.request.user
            ).count()
            context["clinical_reports_to_review_count"] = ClinicalReport.objects.filter(
                module_offering__coordinator=self.request.user,
                status=ReportStatus.SUBMITTED,
            ).count()
            return context

        context["clinical_reports_count"] = ClinicalReport.objects.count()
        context["teaching_reports_count"] = ClinicalTeachingReport.objects.count()
        context["submitted_reports_count"] = ClinicalReport.objects.filter(
            status=ReportStatus.SUBMITTED
        ).count()
        context["submitted_teaching_reports_count"] = ClinicalTeachingReport.objects.filter(
            status=ReportStatus.SUBMITTED
        ).count()

        return context


class ClinicalReportListView(LoginRequiredMixin, ListView):
    model = ClinicalReport
    template_name = "reports/clinical_report_list.html"
    context_object_name = "reports"
    paginate_by = 20
    login_url = "account_login"

    def get_queryset(self):
        queryset = ClinicalReport.objects.select_related(
            "student",
            "student__student_profile",
            "module_offering",
            "module_offering__module",
            "reviewed_by",
        )

        role = getattr(self.request.user, "role", None)

        if role == UserRole.STUDENT:
            queryset = queryset.filter(student=self.request.user)
        elif role == UserRole.LECTURER:
            queryset = queryset.filter(module_offering__coordinator=self.request.user)
        elif role not in [
            UserRole.IT_ADMIN,
            UserRole.ADMINISTRATION,
            UserRole.LAB_COORDINATOR,
        ]:
            queryset = queryset.none()

        return queryset.order_by("-created_at")


class ClinicalReportCreateView(StudentRequiredMixin, CreateView):
    model = ClinicalReport
    form_class = ClinicalReportForm
    template_name = "reports/clinical_report_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["student"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.student = self.request.user
        messages.success(
            self.request,
            "Clinical report saved as draft. Submit it when ready.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "reports:clinical_report_detail",
            kwargs={"pk": self.object.pk},
        )


class ClinicalReportUpdateView(StudentRequiredMixin, UpdateView):
    model = ClinicalReport
    form_class = ClinicalReportForm
    template_name = "reports/clinical_report_form.html"

    def get_queryset(self):
        return ClinicalReport.objects.filter(
            student=self.request.user,
            status__in=[
                ReportStatus.DRAFT,
                ReportStatus.REVISION_REQUESTED,
            ],
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["student"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy(
            "reports:clinical_report_detail",
            kwargs={"pk": self.object.pk},
        )


class ClinicalReportDetailView(LoginRequiredMixin, DetailView):
    model = ClinicalReport
    template_name = "reports/clinical_report_detail.html"
    context_object_name = "report"
    login_url = "account_login"

    def get_queryset(self):
        queryset = ClinicalReport.objects.select_related(
            "student",
            "student__student_profile",
            "module_offering",
            "module_offering__module",
            "reviewed_by",
        ).prefetch_related("reviews")

        role = getattr(self.request.user, "role", None)

        if role == UserRole.STUDENT:
            queryset = queryset.filter(student=self.request.user)
        elif role == UserRole.LECTURER:
            queryset = queryset.filter(module_offering__coordinator=self.request.user)
        elif role not in [
            UserRole.IT_ADMIN,
            UserRole.ADMINISTRATION,
            UserRole.LAB_COORDINATOR,
        ]:
            queryset = queryset.none()

        return queryset


class ClinicalReportSubmitView(StudentRequiredMixin, View):
    def post(self, request, pk):
        report = get_object_or_404(
            ClinicalReport,
            pk=pk,
            student=request.user,
        )

        try:
            submit_clinical_report(report=report)
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect("reports:clinical_report_detail", pk=report.pk)

        messages.success(request, "Clinical report submitted successfully.")

        return redirect("reports:clinical_report_detail", pk=report.pk)


class ClinicalReportReviewView(ReportReviewerRequiredMixin, FormView):
    template_name = "reports/report_review_form.html"
    form_class = ReportReviewForm

    def dispatch(self, request, *args, **kwargs):
        self.report = get_object_or_404(ClinicalReport, pk=kwargs["pk"])

        if getattr(request.user, "role", None) == UserRole.LECTURER:
            if self.report.module_offering.coordinator_id != request.user.id:
                messages.error(request, "You can only review reports for your modules.")
                return redirect("reports:clinical_report_list")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            review_clinical_report(
                report=self.report,
                reviewer=self.request.user,
                decision=form.cleaned_data["decision"],
                comments=form.cleaned_data["comments"],
            )
        except Exception as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(self.request, "Clinical report reviewed successfully.")

        return redirect("reports:clinical_report_detail", pk=self.report.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["report_object"] = self.report
        context["report_kind"] = "Clinical Report"
        return context


class ClinicalTeachingReportListView(LoginRequiredMixin, ListView):
    model = ClinicalTeachingReport
    template_name = "reports/teaching_report_list.html"
    context_object_name = "reports"
    paginate_by = 20
    login_url = "account_login"

    def get_queryset(self):
        queryset = ClinicalTeachingReport.objects.select_related(
            "lecturer",
            "module_offering",
            "module_offering__module",
            "reviewed_by",
        )

        role = getattr(self.request.user, "role", None)

        if role == UserRole.LECTURER:
            queryset = queryset.filter(lecturer=self.request.user)
        elif role not in [
            UserRole.IT_ADMIN,
            UserRole.ADMINISTRATION,
        ]:
            queryset = queryset.none()

        return queryset.order_by("-teaching_date")


class ClinicalTeachingReportCreateView(ReportStaffRequiredMixin, CreateView):
    model = ClinicalTeachingReport
    form_class = ClinicalTeachingReportForm
    template_name = "reports/teaching_report_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lecturer"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.lecturer = self.request.user
        messages.success(
            self.request,
            "Clinical teaching report saved as draft.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "reports:teaching_report_detail",
            kwargs={"pk": self.object.pk},
        )


class ClinicalTeachingReportUpdateView(ReportStaffRequiredMixin, UpdateView):
    model = ClinicalTeachingReport
    form_class = ClinicalTeachingReportForm
    template_name = "reports/teaching_report_form.html"

    def get_queryset(self):
        queryset = ClinicalTeachingReport.objects.filter(
            status__in=[
                ReportStatus.DRAFT,
                ReportStatus.REVISION_REQUESTED,
            ]
        )

        if getattr(self.request.user, "role", None) == UserRole.LECTURER:
            queryset = queryset.filter(lecturer=self.request.user)

        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lecturer"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy(
            "reports:teaching_report_detail",
            kwargs={"pk": self.object.pk},
        )


class ClinicalTeachingReportDetailView(LoginRequiredMixin, DetailView):
    model = ClinicalTeachingReport
    template_name = "reports/teaching_report_detail.html"
    context_object_name = "report"
    login_url = "account_login"

    def get_queryset(self):
        queryset = ClinicalTeachingReport.objects.select_related(
            "lecturer",
            "module_offering",
            "module_offering__module",
            "reviewed_by",
        ).prefetch_related("reviews")

        role = getattr(self.request.user, "role", None)

        if role == UserRole.LECTURER:
            queryset = queryset.filter(lecturer=self.request.user)
        elif role not in [
            UserRole.IT_ADMIN,
            UserRole.ADMINISTRATION,
        ]:
            queryset = queryset.none()

        return queryset


class ClinicalTeachingReportSubmitView(ReportStaffRequiredMixin, View):
    def post(self, request, pk):
        report = get_object_or_404(ClinicalTeachingReport, pk=pk)

        if getattr(request.user, "role", None) == UserRole.LECTURER:
            if report.lecturer_id != request.user.id:
                messages.error(request, "You can only submit your own teaching report.")
                return redirect("reports:teaching_report_list")

        try:
            submit_clinical_teaching_report(report=report)
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect("reports:teaching_report_detail", pk=report.pk)

        messages.success(request, "Clinical teaching report submitted successfully.")

        return redirect("reports:teaching_report_detail", pk=report.pk)


class ClinicalTeachingReportReviewView(AdministrationReportRequiredMixin, FormView):
    template_name = "reports/report_review_form.html"
    form_class = ReportReviewForm

    def dispatch(self, request, *args, **kwargs):
        self.report = get_object_or_404(ClinicalTeachingReport, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            review_clinical_teaching_report(
                report=self.report,
                reviewer=self.request.user,
                decision=form.cleaned_data["decision"],
                comments=form.cleaned_data["comments"],
            )
        except Exception as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(
            self.request,
            "Clinical teaching report reviewed successfully.",
        )

        return redirect("reports:teaching_report_detail", pk=self.report.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["report_object"] = self.report
        context["report_kind"] = "Clinical Teaching Report"
        return context


class MyPortfolioView(StudentRequiredMixin, TemplateView):
    template_name = "reports/portfolio_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["portfolio_student"] = self.request.user
        context["summary"] = get_student_portfolio_summary(self.request.user)
        return context


class StudentPortfolioView(ReportStaffRequiredMixin, TemplateView):
    template_name = "reports/portfolio_detail.html"

    def dispatch(self, request, *args, **kwargs):
        User = get_user_model()
        self.portfolio_student = get_object_or_404(
            User,
            pk=kwargs["student_pk"],
            role=UserRole.STUDENT,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["portfolio_student"] = self.portfolio_student
        context["summary"] = get_student_portfolio_summary(self.portfolio_student)
        return context


class PortfolioItemCreateView(LoginRequiredMixin, CreateView):
    model = PortfolioItem
    form_class = PortfolioItemForm
    template_name = "reports/portfolio_item_form.html"
    login_url = "account_login"

    def dispatch(self, request, *args, **kwargs):
        role = getattr(request.user, "role", None)

        if role == UserRole.STUDENT:
            self.portfolio_student = request.user
        else:
            User = get_user_model()
            self.portfolio_student = get_object_or_404(
                User,
                pk=kwargs["student_pk"],
                role=UserRole.STUDENT,
            )

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["student"] = self.portfolio_student
        return kwargs

    def form_valid(self, form):
        form.instance.student = self.portfolio_student
        form.instance.created_by = self.request.user
        messages.success(self.request, "Portfolio item added successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        if getattr(self.request.user, "role", None) == UserRole.STUDENT:
            return reverse_lazy("reports:my_portfolio")

        return reverse_lazy(
            "reports:student_portfolio",
            kwargs={"student_pk": self.portfolio_student.pk},
        )


class ClinicalReportAttachmentDownloadView(LoginRequiredMixin, View):
    login_url = "account_login"

    def get(self, request, pk):
        report = get_object_or_404(ClinicalReport, pk=pk)

        role = getattr(request.user, "role", None)

        allowed = (
            report.student_id == request.user.id
            or role in [
                UserRole.IT_ADMIN,
                UserRole.ADMINISTRATION,
                UserRole.LAB_COORDINATOR,
            ]
            or (
                role == UserRole.LECTURER
                and report.module_offering.coordinator_id == request.user.id
            )
        )

        if not allowed:
            raise Http404

        if not report.attachment:
            raise Http404

        return FileResponse(
            report.attachment.open("rb"),
            as_attachment=True,
            filename=report.attachment.name.split("/")[-1],
        )


class TeachingReportAttachmentDownloadView(AdministrationReportRequiredMixin, View):
    def get(self, request, pk):
        report = get_object_or_404(ClinicalTeachingReport, pk=pk)

        if not report.attachment:
            raise Http404

        return FileResponse(
            report.attachment.open("rb"),
            as_attachment=True,
            filename=report.attachment.name.split("/")[-1],
        )


class ClinicalReportExportView(AdministrationReportRequiredMixin, View):
    def get(self, request):
        reports = ClinicalReport.objects.select_related(
            "student",
            "student__student_profile",
            "module_offering",
            "module_offering__module",
            "reviewed_by",
        ).order_by("-created_at")

        return export_clinical_reports_workbook(reports)


class ClinicalTeachingReportExportView(AdministrationReportRequiredMixin, View):
    def get(self, request):
        reports = ClinicalTeachingReport.objects.select_related(
            "lecturer",
            "module_offering",
            "module_offering__module",
            "reviewed_by",
        ).order_by("-teaching_date")

        return export_clinical_teaching_reports_workbook(reports)


class PortfolioExportView(LoginRequiredMixin, View):
    login_url = "account_login"

    def get(self, request, student_pk=None):
        role = getattr(request.user, "role", None)

        if role == UserRole.STUDENT:
            student = request.user
        else:
            User = get_user_model()
            student = get_object_or_404(
                User,
                pk=student_pk,
                role=UserRole.STUDENT,
            )

        summary = get_student_portfolio_summary(student)

        return export_student_portfolio_workbook(student, summary)