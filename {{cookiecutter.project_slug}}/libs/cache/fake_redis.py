from typing import Any

from django_redis.cache import RedisCache as BaseRedisCache
from fakeredis import FakeRedis
from fakeredis import FakeServer

from .client import EnhancedRedisClient
from .mixins import RedisCommonMixin
from .mixins import RedisHashMixin
from .mixins import RedisListMixin
from .mixins import RedisLockMixin
from .mixins import RedisSetMixin
from .mixins import RedisSortedSetMixin


class FakeEnhancedRedisClient(EnhancedRedisClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fake_server = FakeServer()
        self._fake_client = FakeRedis(server=self._fake_server, decode_responses=False)

    def connect(self, index: int = 0):
        return self._fake_client

    def get_client(self, write: bool = True, tried=None):
        return self._fake_client

    def close(self):
        if hasattr(self, "_fake_client"):
            self._fake_client.flushall()
            del self._fake_client
        if hasattr(self, "_fake_server"):
            del self._fake_server


class FakeEnhancedRedisCache(
    RedisCommonMixin,
    RedisHashMixin,
    RedisListMixin,
    RedisSetMixin,
    RedisSortedSetMixin,
    RedisLockMixin,
    BaseRedisCache,
):
    def __init__(self, server: str, params: dict[str, Any]):
        options = params.get("OPTIONS", {})
        options["CLIENT_CLASS"] = "libs.cache.fake_redis.FakeEnhancedRedisClient"
        params["OPTIONS"] = options

        super().__init__(server, params)
        self._internal_prefix = None
        self.original_key_func = self.key_func

    def set_internal_prefix(self, value):
        self._internal_prefix = value
        self.key_func = self._dynamic_key_func

    def _dynamic_key_func(self, key, key_prefix, version):
        if self._internal_prefix:
            key = f"{self._internal_prefix}:{key}"
        return self.original_key_func(key, key_prefix, version)
