from allauth.account.signals import password_changed, password_reset, password_set
from django.dispatch import receiver


@receiver([password_changed, password_reset, password_set])
def clear_must_change_password_flag(request, user, **kwargs):
    if user and getattr(user, "must_change_password", False):
        user.must_change_password = False
        user.save(update_fields=["must_change_password"])