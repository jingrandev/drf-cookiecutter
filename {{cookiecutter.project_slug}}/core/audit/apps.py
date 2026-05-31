import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuditConfig(AppConfig):
    name = "core.audit"
    label = "audit"
    verbose_name = _("Audit")

    def ready(self):
        with contextlib.suppress(ImportError):
            import core.audit.signals  # noqa: F401
