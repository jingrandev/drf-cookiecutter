from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Sequence
from typing import Any
from typing import Generic
from typing import TypeVar

from django.db import models
from django.db import transaction

ModelT = TypeVar("ModelT", bound=models.Model)
EntityT = TypeVar("EntityT")
KeyT = TypeVar("EntityT")
QuerySetScope = Callable[[models.QuerySet], models.QuerySet]


class SyncResult(tuple, Generic[KeyT]):
    def __new__(
        cls,
        *,
        created: int,
        updated: int,
        skipped: int,
        created_keys: tuple[KeyT, ...] = (),
        updated_keys: tuple[KeyT, ...] = (),
        skipped_keys: tuple[KeyT, ...] = (),
    ) -> "SyncResult[KeyT]":
        obj = super().__new__(cls, (created, updated, skipped))
        obj.created_keys = created_keys
        obj.updated_keys = updated_keys
        obj.skipped_keys = skipped_keys
        return obj

    @property
    def created(self) -> int:
        return int(self[0])

    @property
    def updated(self) -> int:
        return int(self[1])

    @property
    def skipped(self) -> int:
        return int(self[2])

    @property
    def changed_keys(self) -> tuple[KeyT, ...]:
        if not self.created_keys and not self.updated_keys:
            return ()
        return self.created_keys + self.updated_keys


def bulk_sync_to_db(
    *,
    entities: Iterable[EntityT],
    model_cls: type[ModelT],
    model_key_field: str,
    get_entity_key: Callable[[EntityT], KeyT | None],
    build_create: Callable[[EntityT], ModelT] | None,
    apply_update: Callable[[ModelT, EntityT], bool],
    filter_entity: Callable[[EntityT], bool] | None,
    update_fields: Sequence[str],
    batch_size: int = 500,
    ignore_create_conflicts: bool = True,
    scope_queryset: QuerySetScope | None = None,
    existing_queryset: models.QuerySet | None = None,
    collect_keys: bool = False,
) -> SyncResult[KeyT]:
    entity_list = list(entities)
    if filter_entity is not None:
        entity_list = [entity for entity in entity_list if filter_entity(entity)]
    if not entity_list:
        return SyncResult(created=0, updated=0, skipped=0)

    keys: list[KeyT] = []
    for entity in entity_list:
        key = get_entity_key(entity)
        if key is None:
            continue
        keys.append(key)
    if not keys:
        return SyncResult(created=0, updated=0, skipped=len(entity_list))

    filter_kwargs = {f"{model_key_field}__in": keys}
    existing_qs = (
        existing_queryset if existing_queryset is not None else model_cls.objects.all()
    )
    existing_qs = existing_qs.filter(**filter_kwargs)
    if scope_queryset:
        existing_qs = scope_queryset(existing_qs)
    existing_map: dict[Any, ModelT] = {
        getattr(obj, model_key_field): obj for obj in existing_qs
    }

    to_create: list[ModelT] = []
    to_update: list[ModelT] = []
    skipped = 0
    created_keys: list[KeyT] = []
    updated_keys: list[KeyT] = []
    skipped_keys: list[KeyT] = []

    for entity in entity_list:
        key = get_entity_key(entity)
        if key is None:
            skipped += 1
            continue

        existing = existing_map.get(key)
        if existing is not None:
            if apply_update(existing, entity):
                to_update.append(existing)
                if collect_keys:
                    updated_keys.append(key)
            continue

        if build_create is None:
            skipped += 1
            if collect_keys:
                skipped_keys.append(key)
            continue

        model_obj = build_create(entity)
        if model_obj is None:
            skipped += 1
            if collect_keys:
                skipped_keys.append(key)
            continue
        to_create.append(model_obj)
        if collect_keys:
            created_keys.append(key)

    if not to_create and not to_update:
        return SyncResult(
            created=0,
            updated=0,
            skipped=skipped,
            skipped_keys=tuple(skipped_keys) if collect_keys else (),
        )

    with transaction.atomic():
        if to_create:
            model_cls.objects.bulk_create(
                to_create,
                batch_size=batch_size,
                ignore_conflicts=ignore_create_conflicts,
            )
        if to_update:
            update_qs = (
                existing_queryset
                if existing_queryset is not None
                else model_cls.objects.all()
            )
            update_qs.bulk_update(
                to_update,
                list(update_fields),
                batch_size=batch_size,
            )

    return SyncResult(
        created=len(to_create),
        updated=len(to_update),
        skipped=skipped,
        created_keys=tuple(created_keys) if collect_keys else (),
        updated_keys=tuple(updated_keys) if collect_keys else (),
        skipped_keys=tuple(skipped_keys) if collect_keys else (),
    )
