import abc
import dataclasses
from typing import Any

from django.db import transaction


class CommandRegistry:
    def __init__(self):
        self._registry: dict[str, type["CommandType"]] = {}

    def register(self, command_type_cls: type["CommandType"]):
        if not issubclass(command_type_cls, CommandType):
            raise TypeError(f"{command_type_cls} must be a subclass of CommandType")
        type_name = command_type_cls.type
        if type_name in self._registry:
            raise ValueError(f"Command type '{type_name}' is already registered")
        self._registry[type_name] = command_type_cls
        return command_type_cls

    def get(self, type_name: str) -> type["CommandType"]:
        try:
            return self._registry[type_name]
        except KeyError:
            raise ValueError(f"Command type '{type_name}' is not registered")

    def __contains__(self, type_name: str) -> bool:
        return type_name in self._registry

    def __iter__(self):
        return iter(self._registry.values())

    def get_all(self) -> dict[str, type["CommandType"]]:
        return dict(self._registry)


@dataclasses.dataclass(frozen=True)
class CommandDescription:
    short: str = ""
    long: str = ""
    context: str = ""


class _CommandTypeMeta(abc.ABCMeta):
    def __call__(cls, *args, **kwargs):
        raise TypeError(
            f"{cls.__name__} cannot be instantiated. "
            f"Use {cls.__name__}.do(user=..., ...) to execute a command."
        )


class CommandType(abc.ABC, metaclass=_CommandTypeMeta):
    type: str = ""
    description: CommandDescription = CommandDescription()

    @classmethod
    def do(cls, user, *args, **kwargs) -> Any:
        result = cls.perform(user, *args, **kwargs)
        cls.register_command(
            user=user,
            params=result,
            scope=cls.scope(user, *args, **kwargs),
        )
        return result

    @classmethod
    @abc.abstractmethod
    def perform(cls, user, *args, **kwargs) -> Any:
        ...

    @classmethod
    def scope(cls, user, *args, **kwargs) -> str:
        return "root"

    @classmethod
    def register_command(cls, *, user, params, scope, **kwargs):
        from core.command.signals import command_executed

        command_executed.send(
            sender=cls,
            user=user,
            command_type=cls,
            params=params,
            scope=scope,
            command=None,
        )


class UndoableCommandType(CommandType):
    @classmethod
    def do(cls, user, *args, **kwargs) -> Any:
        with transaction.atomic():
            result = cls.perform(user, *args, **kwargs)
            cls.register_command(
                user=user,
                params=result,
                scope=cls.scope(user, *args, **kwargs),
            )
            return result

    @classmethod
    def register_command(cls, *, user, params, scope, **kwargs):
        from core.command.models import Command
        from core.command.signals import command_executed

        serialized = (
            dataclasses.asdict(params) if dataclasses.is_dataclass(params) else params
        )
        command = Command.objects.create(
            user=user,
            type=cls.type,
            params=serialized,
            scope=scope,
            description=cls.description.short,
        )
        command_executed.send(
            sender=cls,
            user=user,
            command_type=cls,
            params=serialized,
            scope=scope,
            command=command,
        )
        return command

    @classmethod
    @abc.abstractmethod
    def undo(cls, user, params, command) -> Any:
        ...

    @classmethod
    @abc.abstractmethod
    def redo(cls, user, params, command) -> Any:
        ...


command_registry = CommandRegistry()
