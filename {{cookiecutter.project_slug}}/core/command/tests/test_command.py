import dataclasses

from django.test import TestCase

from core.command.errors import CommandNotFoundError, CommandNotRedoableError, CommandNotUndoableError
from core.command.models import Command
from core.command.registries import CommandType, UndoableCommandType, command_registry
from core.command.scopes import ScopeBuilder
from core.command.services.handler import CommandHandler


class SimpleCommandType(CommandType):
    type = "test.simple"

    @classmethod
    def perform(cls, user, *args, **kwargs):
        return {"detail": "test command"}


@dataclasses.dataclass
class UndoableParams:
    value: int


class UndoableTestCommand(UndoableCommandType):
    type = "test.undoable"

    @classmethod
    def perform(cls, user, *args, **kwargs):
        return UndoableParams(value=kwargs.get("value", 1))

    @classmethod
    def undo(cls, user, params, command):
        pass

    @classmethod
    def redo(cls, user, params, command):
        pass


class ScopedTestCommand(UndoableCommandType):
    type = "test.scoped"

    @classmethod
    def perform(cls, user, *args, **kwargs):
        return {"item_id": kwargs.get("item_id")}

    @classmethod
    def scope(cls, user, *args, **kwargs):
        return ScopeBuilder.object("item", kwargs.get("item_id", 0))

    @classmethod
    def undo(cls, user, params, command):
        pass

    @classmethod
    def redo(cls, user, params, command):
        pass


command_registry.register(SimpleCommandType)
command_registry.register(UndoableTestCommand)
command_registry.register(ScopedTestCommand)


class TestCommandModel(TestCase):
    def test_create_command(self):
        command = Command.objects.create(
            type="test.simple",
            params={"key": "value"},
            scope="root",
        )
        self.assertIsNotNone(command.id)
        self.assertEqual(command.type, "test.simple")
        self.assertEqual(command.params, {"key": "value"})
        self.assertIsNone(command.user)
        self.assertIsNone(command.undone_at)

    def test_command_ordering(self):
        Command.objects.create(type="test.first")
        Command.objects.create(type="test.second")
        commands = Command.objects.all()
        self.assertEqual(commands[0].type, "test.second")
        self.assertEqual(commands[1].type, "test.first")


class TestScopeBuilder(TestCase):
    def test_root(self):
        self.assertEqual(ScopeBuilder.root(), "root")

    def test_object(self):
        self.assertEqual(ScopeBuilder.object("project", 42), "project:42")

    def test_user(self):
        self.assertEqual(ScopeBuilder.user(1), "user:1")

    def test_custom(self):
        self.assertEqual(ScopeBuilder.custom("a", "b", "c"), "a:b:c")


class TestCommandType(TestCase):
    def test_do_calls_perform_and_signal(self):
        result = SimpleCommandType.do(user=None)
        self.assertEqual(result, {"detail": "test command"})

    def test_undoable_do_creates_db_record(self):
        self.assertEqual(Command.objects.count(), 0)
        result = UndoableTestCommand.do(user=None, value=42)
        self.assertIsInstance(result, UndoableParams)
        self.assertEqual(result.value, 42)
        self.assertEqual(Command.objects.count(), 1)
        command = Command.objects.first()
        self.assertEqual(command.type, "test.undoable")
        self.assertEqual(command.params, {"value": 42})

    def test_undoable_do_with_scope(self):
        UndoableTestCommand.do(user=None, value=1)
        command = Command.objects.first()
        self.assertEqual(command.scope, "root")

    def test_scoped_command(self):
        ScopedTestCommand.do(user=None, item_id=99)
        command = Command.objects.first()
        self.assertEqual(command.scope, "item:99")

    def test_cannot_instantiate_command_type(self):
        with self.assertRaises(TypeError):
            SimpleCommandType()


class TestCommandHandler(TestCase):
    def test_undo(self):
        UndoableTestCommand.do(user=None, value=1)
        command = Command.objects.first()
        result = CommandHandler.undo(user=None, command_id=command.id)
        result.refresh_from_db()
        self.assertIsNotNone(result.undone_at)

    def test_redo(self):
        UndoableTestCommand.do(user=None, value=1)
        command = Command.objects.first()
        CommandHandler.undo(user=None, command_id=command.id)
        result = CommandHandler.redo(user=None, command_id=command.id)
        result.refresh_from_db()
        self.assertIsNone(result.undone_at)

    def test_undo_nonexistent_raises(self):
        with self.assertRaises(CommandNotFoundError):
            CommandHandler.undo(user=None, command_id=99999)

    def test_redo_not_undone_raises(self):
        UndoableTestCommand.do(user=None, value=1)
        command = Command.objects.first()
        with self.assertRaises(CommandNotFoundError):
            CommandHandler.redo(user=None, command_id=command.id)

    def test_undo_non_undoable_raises(self):
        Command.objects.create(type="test.simple", params={}, scope="root")
        command = Command.objects.first()
        with self.assertRaises(CommandNotUndoableError):
            CommandHandler.undo(user=None, command_id=command.id)

    def test_redo_non_undoable_raises(self):
        command = Command.objects.create(type="test.simple", params={}, scope="root")
        command.undone_at = command.created_at
        command.save()
        with self.assertRaises(CommandNotRedoableError):
            CommandHandler.redo(user=None, command_id=command.id)
