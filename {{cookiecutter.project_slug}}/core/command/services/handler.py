from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.command.errors import CommandNotFoundError, CommandNotRedoableError, CommandNotUndoableError
from core.command.models import Command
from core.command.registries import UndoableCommandType
from core.command.registries import command_registry


class CommandHandler:
    @classmethod
    def undo(cls, user, command_id: int) -> Command:
        with transaction.atomic():
            try:
                command = Command.objects.select_for_update(of=("self",)).get(
                    pk=command_id, user=user, undone_at__isnull=True
                )
            except Command.DoesNotExist:
                raise CommandNotFoundError()

            command_type_cls = command_registry.get(command.type)
            if not issubclass(command_type_cls, UndoableCommandType):
                raise CommandNotUndoableError()

            command_type_cls.undo(user, command.params, command)
            command.undone_at = timezone.now()
            command.error = None
            command.save(update_fields=["undone_at", "error", "updated_at"])

        return command

    @classmethod
    def redo(cls, user, command_id: int) -> Command:
        with transaction.atomic():
            try:
                command = Command.objects.select_for_update(of=("self",)).get(
                    pk=command_id, user=user, undone_at__isnull=False
                )
            except Command.DoesNotExist:
                raise CommandNotFoundError()

            command_type_cls = command_registry.get(command.type)
            if not issubclass(command_type_cls, UndoableCommandType):
                raise CommandNotRedoableError()

            command_type_cls.redo(user, command.params, command)
            command.undone_at = None
            command.error = None
            command.save(update_fields=["undone_at", "error", "updated_at"])

        return command

    @classmethod
    def cleanup(cls) -> int:
        retention_days = getattr(settings, "COMMAND_RETENTION_DAYS", 90)
        cutoff = timezone.now() - timezone.timedelta(days=retention_days)
        qs = Command.objects.filter(created_at__lt=cutoff)
        count, _ = qs.delete()
        return count
