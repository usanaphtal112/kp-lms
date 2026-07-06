from django.conf import settings
from django.shortcuts import redirect
from django.urls import Resolver404, resolve


class MustChangePasswordMiddleware:
    ALLOWED_URL_NAMES = {
        "account_change_password",
        "account_logout",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)

        if user and user.is_authenticated and getattr(user, "must_change_password", False):
            if not self.is_allowed_path(request):
                return redirect("account_change_password")

        return self.get_response(request)

    def is_allowed_path(self, request):
        path = request.path

        if path.startswith(settings.STATIC_URL):
            return True

        if settings.MEDIA_URL and path.startswith(settings.MEDIA_URL):
            return True

        if path.startswith("/admin/"):
            return True

        try:
            match = resolve(path)
        except Resolver404:
            return False

        return match.url_name in self.ALLOWED_URL_NAMES