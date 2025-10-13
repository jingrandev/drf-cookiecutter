from django.db.utils import IntegrityError
from django.test import TransactionTestCase

from core.tests.models import (
    DummyModel,
    UniqueFieldModel,
    MultiUniqueFieldModel,
    CustomPKModel,
)


class TestSoftDelete(TransactionTestCase):
    """Test cases for soft delete functionality."""


    def test_single_object_delete(self):
        """Test soft deletion of a single object."""
        obj = DummyModel.objects.create(name="Test Object")
        original_id = obj.id
        
        assert obj.id_copy == ""
        
        obj.delete()
        obj.refresh_from_db()
        
        assert obj.is_deleted is True
        assert obj.deleted_at is not None
        assert obj.id_copy == str(original_id)

    def test_queryset_delete(self):
        """Test batch soft deletion using QuerySet.delete()."""
        obj1 = DummyModel.objects.create(name="Test Object 1")
        obj2 = DummyModel.objects.create(name="Test Object 2")
        obj3 = DummyModel.objects.create(name="Test Object 3")
        
        original_ids = [obj1.id, obj2.id, obj3.id]
        
        for obj in DummyModel.objects.all():
            assert obj.id_copy == ""
        
        DummyModel.objects.all().delete()
        
        for obj, original_id in zip(DummyModel.objects.all(), original_ids):
            assert obj.is_deleted is True
            assert obj.deleted_at is not None
            assert obj.id_copy == str(original_id)

    def test_unique_field_constraint(self):
        """Test models with unique field constraints."""
        obj1 = UniqueFieldModel.objects.create(
            name="Unique Name",
            email="test@example.com",
            code="CODE1"
        )
        
        with self.assertRaises(IntegrityError):
            UniqueFieldModel.objects.create(
                name="Unique Name",
                email="different@example.com",
                code="CODE2"
            )
        
        obj1.delete()
        obj1.refresh_from_db()
        
        assert obj1.is_deleted is True
        assert obj1.id_copy != ""
        
        obj2 = UniqueFieldModel.objects.create(
            name="Unique Name",
            email="test@example.com",
            code="CODE1"
        )
        
        assert obj2.id != obj1.id
        assert obj2.name == obj1.name
        assert obj2.email == obj1.email
        assert obj2.is_deleted is False
        assert obj2.id_copy == ""

    def test_multi_unique_field_constraint(self):
        """Test models with multi-field unique constraints."""
        obj1 = MultiUniqueFieldModel.objects.create(
            name="Multi Unique",
            code="MULTI_CODE"
        )
        
        with self.assertRaises(IntegrityError):
            MultiUniqueFieldModel.objects.create(
                name="Multi Unique",
                code="MULTI_CODE"
            )
        
        obj1.delete()
        obj1.refresh_from_db()
        
        assert obj1.is_deleted is True
        assert obj1.id_copy != ""
        
        obj2 = MultiUniqueFieldModel.objects.create(
            name="Multi Unique",
            code="MULTI_CODE"
        )
        
        assert obj2.id != obj1.id
        assert obj2.name == obj1.name
        assert obj2.code == obj1.code
        assert obj2.is_deleted is False
        assert obj2.id_copy == ""

    def test_custom_pk_soft_delete(self):
        """Test soft deletion of models with custom primary key types."""
        obj = CustomPKModel.objects.create(
            id="custom-pk-1",
            name="Custom PK Object",
            code="CUSTOM_CODE"
        )
        
        assert obj.id_copy == ""
        
        obj.delete()
        obj.refresh_from_db()
        
        assert obj.is_deleted is True
        assert obj.deleted_at is not None
        assert obj.id_copy == "custom-pk-1"
        
        obj2 = CustomPKModel.objects.create(
            id="custom-pk-2",
            name="Another Custom PK Object",
            code="CUSTOM_CODE"
        )
        
        assert obj2.id != obj.id
        assert obj2.code == obj.code

    def test_restore_object(self):
        """Test restoration of soft-deleted objects."""
        obj = DummyModel.objects.create(name="Test Object")
        original_id = obj.id
        
        obj.delete()
        obj.refresh_from_db()
        
        assert obj.is_deleted is True
        assert obj.id_copy == str(original_id)
        
        obj.restore()
        
        obj.refresh_from_db()
        
        assert obj.is_deleted is False
        assert obj.deleted_at is None
        assert obj.id_copy == ""

    def test_queryset_restore(self):
        """Test batch restoration using QuerySet.restore()."""
        DummyModel.objects.create(name="Test Object 1")
        DummyModel.objects.create(name="Test Object 2")

        DummyModel.objects.all().delete()
        
        for obj in DummyModel.all_objects.all():
            assert obj.is_deleted is True
            assert obj.deleted_at is not None
        
        DummyModel.all_objects.deleted().restore()
        
        for obj in DummyModel.objects.all():
            assert obj.is_deleted is False
            assert obj.deleted_at is None
            assert obj.id_copy == ""

    def test_multiple_deletes_of_same_object(self):
        """Test multiple soft deletions of the same object."""
        obj = DummyModel.objects.create(name="Test Object")
        original_id = obj.id
        
        obj.delete()
        obj.refresh_from_db()
        
        assert obj.is_deleted is True
        assert obj.id_copy == str(original_id)
        
        first_deleted_at = obj.deleted_at
        
        obj.delete()
        obj.refresh_from_db()
        
        assert obj.is_deleted is True
        assert obj.id_copy == str(original_id)
        assert obj.deleted_at > first_deleted_at

    def test_hard_delete(self):
        """Test hard deletion functionality."""
        obj = DummyModel.objects.create(name="Test Object")
        obj_id = obj.id
        
        DummyModel.objects.filter(id=obj_id).hard_delete()
        
        assert DummyModel.objects.filter(id=obj_id).exists() is False
        assert DummyModel.all_objects.filter(id=obj_id).exists() is False
        
    def test_unique_constraint_after_restore(self):
        """Test unique constraint behavior after restoring soft-deleted objects."""
        obj1 = UniqueFieldModel.objects.create(
            name="Restore Test",
            email="restore@example.com",
            code="RESTORE"
        )
        
        obj1.delete()
        
        obj2 = UniqueFieldModel.objects.create(
            name="Restore Test",
            email="restore@example.com",
            code="RESTORE"
        )
        with self.assertRaises(IntegrityError):
            obj1.restore()
        
        obj1.refresh_from_db()
        obj2.refresh_from_db()
        
        assert obj1.is_deleted is True
        assert obj2.is_deleted is False
        assert obj1.name == obj2.name
        assert obj1.email == obj2.email
        assert obj1.id_copy != ""
        assert obj2.id_copy == ""
