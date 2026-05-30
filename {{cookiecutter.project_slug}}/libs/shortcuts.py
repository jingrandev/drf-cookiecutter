from typing import Any
from typing import TypeVar

T = TypeVar("T")


def get_fk_instance(obj: Any, attr_name: str, default: T | None = None) -> T | None:
    if obj is None:
        return default

    value = getattr(obj, attr_name, None)
    return value if value is not None else default
