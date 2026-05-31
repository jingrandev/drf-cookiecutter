from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.audit.errors import ActionNotFoundError, ActionNotRedoableError, ActionNotUndoableError
from core.audit.models import Action
from core.audit.registries import UndoableActionType
from core.audit.registries import action_registry


class ActionHandler:
    @classmethod
    def undo(cls, user, action_id: int) -> Action:
        try:
            action = Action.objects.select_for_update(of=("self",)).get(
                pk=action_id, user=user, undone_at__isnull=True
            )
        except Action.DoesNotExist:
            raise ActionNotFoundError()

        action_type_cls = action_registry.get(action.type)
        if not issubclass(action_type_cls, UndoableActionType):
            raise ActionNotUndoableError()

        with transaction.atomic():
            action_type_cls.undo(user, action.params, action)
            action.undone_at = timezone.now()
            action.error = None
            action.save(update_fields=["undone_at", "error", "updated_at"])

        return action

    @classmethod
    def redo(cls, user, action_id: int) -> Action:
        try:
            action = Action.objects.select_for_update(of=("self",)).get(
                pk=action_id, user=user, undone_at__isnull=False
            )
        except Action.DoesNotExist:
            raise ActionNotFoundError()

        action_type_cls = action_registry.get(action.type)
        if not issubclass(action_type_cls, UndoableActionType):
            raise ActionNotRedoableError()

        with transaction.atomic():
            action_type_cls.redo(user, action.params, action)
            action.undone_at = None
            action.error = None
            action.save(update_fields=["undone_at", "error", "updated_at"])

        return action

    @classmethod
    def cleanup(cls) -> int:
        retention_days = getattr(settings, "ACTION_RETENTION_DAYS", 90)
        cutoff = timezone.now() - timezone.timedelta(days=retention_days)
        qs = Action.objects.filter(created_at__lt=cutoff)
        count, _ = qs.delete()
        return count
