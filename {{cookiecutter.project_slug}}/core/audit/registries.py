import abc
import dataclasses
from typing import Any

from django.db import transaction


class ActionRegistry:
    def __init__(self):
        self._registry: dict[str, type["ActionType"]] = {}

    def register(self, action_type_cls: type["ActionType"]):
        if not issubclass(action_type_cls, ActionType):
            raise TypeError(f"{action_type_cls} must be a subclass of ActionType")
        type_name = action_type_cls.type
        if type_name in self._registry:
            raise ValueError(f"Action type '{type_name}' is already registered")
        self._registry[type_name] = action_type_cls
        return action_type_cls

    def get(self, type_name: str) -> type["ActionType"]:
        try:
            return self._registry[type_name]
        except KeyError:
            raise ValueError(f"Action type '{type_name}' is not registered")

    def __contains__(self, type_name: str) -> bool:
        return type_name in self._registry

    def __iter__(self):
        return iter(self._registry.values())

    def get_all(self) -> dict[str, type["ActionType"]]:
        return dict(self._registry)


@dataclasses.dataclass(frozen=True)
class ActionTypeDescription:
    short: str = ""
    long: str = ""
    context: str = ""


class ActionType(abc.ABC):
    type: str = ""
    description: ActionTypeDescription = ActionTypeDescription()

    @classmethod
    def do(cls, *args, **kwargs) -> Any:
        result = cls.perform(*args, **kwargs)
        cls.register_action(
            user=kwargs.get("user"),
            params=result,
            scope=cls.scope(*args, **kwargs),
        )
        return result

    @classmethod
    @abc.abstractmethod
    def perform(cls, *args, **kwargs) -> Any:
        ...

    @classmethod
    def scope(cls, *args, **kwargs) -> str:
        return "root"

    @classmethod
    def register_action(cls, *, user, params, scope, **kwargs):
        from core.audit.signals import action_done

        action_done.send(
            sender=cls,
            user=user,
            action_type=cls,
            params=params,
            scope=scope,
        )


class UndoableActionType(ActionType):
    @classmethod
    def do(cls, *args, **kwargs) -> Any:
        with transaction.atomic():
            result = cls.perform(*args, **kwargs)
            cls.register_action(
                user=kwargs.get("user"),
                params=result,
                scope=cls.scope(*args, **kwargs),
            )
            return result

    @classmethod
    def register_action(cls, *, user, params, scope, **kwargs):
        from core.audit.models import Action
        from core.audit.signals import action_done

        serialized = (
            dataclasses.asdict(params) if dataclasses.is_dataclass(params) else params
        )
        action = Action.objects.create(
            user=user,
            type=cls.type,
            params=serialized,
            scope=scope,
            description=cls.description.short,
        )
        action_done.send(
            sender=cls,
            user=user,
            action=action,
            action_type=cls,
            params=serialized,
            scope=scope,
        )
        return action

    @classmethod
    @abc.abstractmethod
    def undo(cls, user, params, action) -> Any:
        ...

    @classmethod
    @abc.abstractmethod
    def redo(cls, user, params, action) -> Any:
        ...


action_registry = ActionRegistry()
