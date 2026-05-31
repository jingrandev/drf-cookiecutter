import dataclasses

from django.test import TestCase

from core.audit.errors import ActionNotFoundError, ActionNotRedoableError, ActionNotUndoableError
from core.audit.models import Action
from core.audit.registries import ActionType, UndoableActionType, action_registry
from core.audit.scopes import ScopeBuilder
from core.audit.services.handler import ActionHandler


class SimpleActionType(ActionType):
    type = "test.simple"

    @classmethod
    def perform(cls, user, *args, **kwargs):
        return {"detail": "test action"}


@dataclasses.dataclass
class UndoableParams:
    value: int


class UndoableTestAction(UndoableActionType):
    type = "test.undoable"

    @classmethod
    def perform(cls, user, *args, **kwargs):
        return UndoableParams(value=kwargs.get("value", 1))

    @classmethod
    def undo(cls, user, params, action):
        pass

    @classmethod
    def redo(cls, user, params, action):
        pass


class ScopedTestAction(UndoableActionType):
    type = "test.scoped"

    @classmethod
    def perform(cls, user, *args, **kwargs):
        return {"item_id": kwargs.get("item_id")}

    @classmethod
    def scope(cls, user, *args, **kwargs):
        return ScopeBuilder.object("item", kwargs.get("item_id", 0))

    @classmethod
    def undo(cls, user, params, action):
        pass

    @classmethod
    def redo(cls, user, params, action):
        pass


action_registry.register(SimpleActionType)
action_registry.register(UndoableTestAction)
action_registry.register(ScopedTestAction)


class TestActionModel(TestCase):
    def test_create_action(self):
        action = Action.objects.create(
            type="test.simple",
            params={"key": "value"},
            scope="root",
        )
        self.assertIsNotNone(action.id)
        self.assertEqual(action.type, "test.simple")
        self.assertEqual(action.params, {"key": "value"})
        self.assertIsNone(action.user)
        self.assertIsNone(action.undone_at)

    def test_action_ordering(self):
        Action.objects.create(type="test.first")
        Action.objects.create(type="test.second")
        actions = Action.objects.all()
        self.assertEqual(actions[0].type, "test.second")
        self.assertEqual(actions[1].type, "test.first")


class TestScopeBuilder(TestCase):
    def test_root(self):
        self.assertEqual(ScopeBuilder.root(), "root")

    def test_object(self):
        self.assertEqual(ScopeBuilder.object("project", 42), "project:42")

    def test_user(self):
        self.assertEqual(ScopeBuilder.user(1), "user:1")

    def test_custom(self):
        self.assertEqual(ScopeBuilder.custom("a", "b", "c"), "a:b:c")


class TestActionType(TestCase):
    def test_do_calls_perform_and_signal(self):
        result = SimpleActionType.do(user=None)
        self.assertEqual(result, {"detail": "test action"})

    def test_undoable_do_creates_db_record(self):
        self.assertEqual(Action.objects.count(), 0)
        result = UndoableTestAction.do(user=None, value=42)
        self.assertIsInstance(result, UndoableParams)
        self.assertEqual(result.value, 42)
        self.assertEqual(Action.objects.count(), 1)
        action = Action.objects.first()
        self.assertEqual(action.type, "test.undoable")
        self.assertEqual(action.params, {"value": 42})

    def test_undoable_do_with_scope(self):
        UndoableTestAction.do(user=None, value=1)
        action = Action.objects.first()
        self.assertEqual(action.scope, "root")

    def test_scoped_action(self):
        ScopedTestAction.do(user=None, item_id=99)
        action = Action.objects.first()
        self.assertEqual(action.scope, "item:99")

    def test_cannot_instantiate_action_type(self):
        with self.assertRaises(TypeError):
            SimpleActionType()


class TestActionHandler(TestCase):
    def test_undo(self):
        UndoableTestAction.do(user=None, value=1)
        action = Action.objects.first()
        result = ActionHandler.undo(user=None, action_id=action.id)
        result.refresh_from_db()
        self.assertIsNotNone(result.undone_at)

    def test_redo(self):
        UndoableTestAction.do(user=None, value=1)
        action = Action.objects.first()
        ActionHandler.undo(user=None, action_id=action.id)
        result = ActionHandler.redo(user=None, action_id=action.id)
        result.refresh_from_db()
        self.assertIsNone(result.undone_at)

    def test_undo_nonexistent_raises(self):
        with self.assertRaises(ActionNotFoundError):
            ActionHandler.undo(user=None, action_id=99999)

    def test_redo_not_undone_raises(self):
        UndoableTestAction.do(user=None, value=1)
        action = Action.objects.first()
        with self.assertRaises(ActionNotFoundError):
            ActionHandler.redo(user=None, action_id=action.id)

    def test_undo_non_undoable_raises(self):
        Action.objects.create(type="test.simple", params={}, scope="root")
        action = Action.objects.first()
        with self.assertRaises(ActionNotUndoableError):
            ActionHandler.undo(user=None, action_id=action.id)

    def test_redo_non_undoable_raises(self):
        action = Action.objects.create(type="test.simple", params={}, scope="root")
        action.undone_at = action.created_at
        action.save()
        with self.assertRaises(ActionNotRedoableError):
            ActionHandler.redo(user=None, action_id=action.id)
