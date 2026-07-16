from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView

from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "notifications/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 30
    login_url = "account_login"

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
        ).order_by("-created_at")


class NotificationReadView(LoginRequiredMixin, View):
    login_url = "account_login"

    def post(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            recipient=request.user,
        )
        notification.mark_read()

        if notification.url:
            return redirect(notification.url)

        return redirect("notifications:list")


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    login_url = "account_login"

    def post(self, request):
        Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)

        return redirect("notifications:list")