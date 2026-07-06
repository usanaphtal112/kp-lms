from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, FormView, ListView, TemplateView, UpdateView

from .forms import (
    AdminPasswordResetForm,
    StaffAccountCreateForm,
    StudentAccountCreateForm,
    UserFilterForm,
    UserUpdateForm,
)
from .mixins import ITAdminRequiredMixin
from .models import AccountAction, AccountActionLog
from .services import assign_user_group, log_account_action, set_user_active_status


class AccountDashboardView(ITAdminRequiredMixin, TemplateView):
    template_name = "accounts/dashboard.html"


class UserListView(ITAdminRequiredMixin, ListView):
    model = get_user_model()
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        User = get_user_model()

        queryset = (
            User.objects.select_related("student_profile", "staff_profile")
            .prefetch_related("groups")
            .order_by("role", "first_name", "last_name", "username")
        )

        form = UserFilterForm(self.request.GET)

        if form.is_valid():
            q = form.cleaned_data.get("q")
            role = form.cleaned_data.get("role")
            status = form.cleaned_data.get("status")

            if q:
                queryset = queryset.filter(
                    Q(username__icontains=q)
                    | Q(first_name__icontains=q)
                    | Q(last_name__icontains=q)
                    | Q(email__icontains=q)
                    | Q(student_profile__registration_number__icontains=q)
                    | Q(staff_profile__staff_number__icontains=q)
                )

            if role:
                queryset = queryset.filter(role=role)

            if status == "active":
                queryset = queryset.filter(is_active=True)
            elif status == "inactive":
                queryset = queryset.filter(is_active=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = UserFilterForm(self.request.GET)
        return context


class StudentAccountCreateView(ITAdminRequiredMixin, FormView):
    template_name = "accounts/user_form.html"
    form_class = StudentAccountCreateForm

    extra_context = {
        "page_title": "Create student account",
        "submit_label": "Create student",
    }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["created_by"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()

        messages.success(
            self.request,
            f"Student account created successfully. Username: {user.username}",
        )

        return redirect("accounts:user_detail", pk=user.pk)


class StaffAccountCreateView(ITAdminRequiredMixin, FormView):
    template_name = "accounts/user_form.html"
    form_class = StaffAccountCreateForm

    extra_context = {
        "page_title": "Create staff account",
        "submit_label": "Create staff",
    }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["created_by"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()

        messages.success(
            self.request,
            f"Staff account created successfully. Username: {user.username}",
        )

        return redirect("accounts:user_detail", pk=user.pk)


class UserDetailView(ITAdminRequiredMixin, DetailView):
    model = get_user_model()
    template_name = "accounts/user_detail.html"
    context_object_name = "target_user"

    def get_queryset(self):
        User = get_user_model()

        return User.objects.select_related(
            "student_profile",
            "staff_profile",
        ).prefetch_related("groups")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account_logs"] = AccountActionLog.objects.filter(
            target_user=self.object
        ).select_related("actor")[:10]
        return context


class UserUpdateView(ITAdminRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"

    extra_context = {
        "page_title": "Update user account",
        "submit_label": "Save changes",
    }

    def form_valid(self, form):
        old_role = self.get_object().role
        response = super().form_valid(form)

        user = self.object
        assign_user_group(user)

        action = AccountAction.ROLE_CHANGED if old_role != user.role else AccountAction.UPDATED

        log_account_action(
            actor=self.request.user,
            target_user=user,
            action=action,
            message="User account updated.",
            metadata={
                "old_role": old_role,
                "new_role": user.role,
            },
        )

        messages.success(self.request, "User account updated successfully.")

        return response

    def get_success_url(self):
        return reverse_lazy("accounts:user_detail", kwargs={"pk": self.object.pk})


class AdminPasswordResetView(ITAdminRequiredMixin, FormView):
    template_name = "accounts/password_reset_by_admin.html"
    form_class = AdminPasswordResetForm

    def dispatch(self, request, *args, **kwargs):
        User = get_user_model()
        self.target_user = get_object_or_404(User, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["target_user"] = self.target_user
        kwargs["reset_by"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["target_user"] = self.target_user
        return context

    def form_valid(self, form):
        form.save()

        messages.success(
            self.request,
            f"Password reset successfully for {self.target_user.username}.",
        )

        return redirect("accounts:user_detail", pk=self.target_user.pk)


class UserActivateView(ITAdminRequiredMixin, View):
    def post(self, request, pk):
        User = get_user_model()
        target_user = get_object_or_404(User, pk=pk)

        set_user_active_status(
            target_user=target_user,
            is_active=True,
            changed_by=request.user,
        )

        messages.success(request, "User account activated.")

        return redirect("accounts:user_detail", pk=target_user.pk)


class UserDeactivateView(ITAdminRequiredMixin, View):
    def post(self, request, pk):
        User = get_user_model()
        target_user = get_object_or_404(User, pk=pk)

        if target_user == request.user:
            messages.error(request, "You cannot deactivate your own account.")
            return redirect("accounts:user_detail", pk=target_user.pk)

        set_user_active_status(
            target_user=target_user,
            is_active=False,
            changed_by=request.user,
        )

        messages.success(request, "User account deactivated.")

        return redirect("accounts:user_detail", pk=target_user.pk)