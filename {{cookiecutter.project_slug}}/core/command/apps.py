import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CommandConfig(AppConfig):
    name = "core.command"
    label = "command"
    verbose_name = _("Command")

    def ready(self):
        with contextlib.suppress(ImportError):
            import core.command.signals  # noqa: F401
