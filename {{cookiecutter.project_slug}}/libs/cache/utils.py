import copy
from collections.abc import Callable

from django.core.cache import caches

from .backend import EnhancedRedisCache


def make_namespaced_cache(
    internal_prefix: str | Callable[[str], str], alias: str = "default"
) -> EnhancedRedisCache:
    if not isinstance(internal_prefix, str | Callable):
        raise TypeError("Argument 'internal_prefix' must be a string or a callable.")

    cache = caches[alias]

    if not isinstance(cache, EnhancedRedisCache):
        if hasattr(cache, "set_internal_prefix"):
            pass
        else:
            raise TypeError(
                f"Cache '{alias}' must be an instance of EnhancedRedisCache to support namespacing. "
                f"Got {type(cache)} instead."
            )

    new_cache = copy.copy(cache)
    new_cache.set_internal_prefix(internal_prefix)

    return new_cache
