import pytest

from apps.core.audit import log_audit
from apps.core.models import AuditAction, AuditLog


@pytest.mark.django_db
def test_global_audit_log_can_record_sensitive_action(admin_user):
    log_audit(
        actor=admin_user,
        action=AuditAction.APPROVE,
        message="Approved test object.",
    )

    assert AuditLog.objects.filter(
        actor=admin_user,
        action=AuditAction.APPROVE,
    ).exists()