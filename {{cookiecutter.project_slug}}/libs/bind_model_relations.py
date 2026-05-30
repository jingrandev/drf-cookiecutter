from collections.abc import Callable
from typing import Any
from typing import TypeVar

from django.db import models
from django.db import transaction

ModelT = TypeVar("ModelT", bound=models.Model)


def bind_fk_by_lookup(
    *,
    source_qs: models.QuerySet,
    source_lookup_field: str,
    source_fk_field: str,
    target_model: type[ModelT],
    target_lookup_field: str,
    target_scope: Callable[[models.QuerySet], models.QuerySet] | None = None,
    normalize_key: Callable[[Any], Any] | None = None,
    normalize_src_key: Callable[[Any], Any] | None = None,
    normalize_tgt_key: Callable[[Any], Any] | None = None,
    only_if_fk_isnull: bool = True,
    clear_if_missing: bool = False,
    batch_size: int = 500,
) -> tuple[int, int, int]:
    if only_if_fk_isnull:
        source_qs = source_qs.filter(**{f"{source_fk_field}__isnull": True})

    source_list = list(source_qs)
    if not source_list:
        return 0, 0, 0

    def apply_src_key(value: Any) -> Any:
        if normalize_src_key is not None:
            return normalize_src_key(value)
        if normalize_key is not None:
            return normalize_key(value)
        return value

    def apply_tgt_key(value: Any) -> Any:
        if normalize_tgt_key is not None:
            return normalize_tgt_key(value)
        if normalize_key is not None:
            return normalize_key(value)
        return value

    source_lookup_values: list[Any] = []
    for obj in source_list:
        raw_value = getattr(obj, source_lookup_field)
        if raw_value is None:
            continue
        mapped = apply_src_key(raw_value)
        if mapped is None:
            continue
        source_lookup_values.append(mapped)

    if not source_lookup_values:
        return 0, len(source_list), 0

    deduped_values = list(set(source_lookup_values))

    target_qs = target_model.objects.filter(
        **{f"{target_lookup_field}__in": deduped_values}
    )
    if target_scope is not None:
        target_qs = target_scope(target_qs)

    target_map: dict[Any, int] = {}
    for target in target_qs.only(target_lookup_field):
        raw_key = getattr(target, target_lookup_field)
        if raw_key is None:
            continue
        mapped_key = apply_tgt_key(raw_key)
        if mapped_key is None:
            continue
        target_map[mapped_key] = target.pk

    bound_count = 0
    skipped_count = 0
    missing_count = 0

    fk_id_attr = f"{source_fk_field}_id"
    to_update: list[models.Model] = []

    for obj in source_list:
        raw_value = getattr(obj, source_lookup_field)
        if raw_value is None:
            skipped_count += 1
            continue

        mapped = apply_src_key(raw_value)
        if mapped is None:
            skipped_count += 1
            continue

        target_pk = target_map.get(mapped)
        if target_pk is None:
            missing_count += 1
            if clear_if_missing and getattr(obj, fk_id_attr, None) is not None:
                setattr(obj, fk_id_attr, None)
                to_update.append(obj)
            continue

        current_fk_id = getattr(obj, fk_id_attr, None)
        if current_fk_id == target_pk:
            skipped_count += 1
            continue

        setattr(obj, fk_id_attr, target_pk)
        to_update.append(obj)
        bound_count += 1

    if not to_update:
        return bound_count, skipped_count, missing_count

    with transaction.atomic():
        source_model_cls = source_list[0].__class__
        source_model_cls.objects.bulk_update(
            to_update,
            [source_fk_field],
            batch_size=batch_size,
        )

    return bound_count, skipped_count, missing_count
