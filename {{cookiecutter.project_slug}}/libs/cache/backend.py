from collections.abc import Callable
from typing import Any

from django_redis.cache import RedisCache as BaseRedisCache

from .client import EnhancedRedisClient
from .mixins import RedisCommonMixin
from .mixins import RedisHashMixin
from .mixins import RedisListMixin
from .mixins import RedisLockMixin
from .mixins import RedisSetMixin
from .mixins import RedisSortedSetMixin


class EnhancedRedisCache(
    RedisCommonMixin,
    RedisHashMixin,
    RedisListMixin,
    RedisSetMixin,
    RedisSortedSetMixin,
    RedisLockMixin,
    BaseRedisCache,
):
    client: EnhancedRedisClient

    def __init__(self, server: str, params: dict[str, Any]):
        options = params.get("OPTIONS", {})
        params["OPTIONS"] = options
        super().__init__(server, params)

        self._internal_prefix: str | Callable[[str], str] | None = None
        self.original_key_func = self.key_func

    @property
    def internal_prefix(self) -> str | Callable[[str], str] | None:
        return self._internal_prefix

    def set_internal_prefix(self, value: str | Callable[[str], str]):
        self._internal_prefix = value
        self.set_key_func(self._dynamic_key_func)

    def set_key_func(self, key_func: Callable):
        self.key_func = key_func

    def _dynamic_key_func(self, key, key_prefix, version):
        if self.internal_prefix:
            if callable(self.internal_prefix):
                key = self.internal_prefix(key)
            else:
                key = f"{self.internal_prefix}:{key}"

        return self.original_key_func(key, key_prefix, version)
