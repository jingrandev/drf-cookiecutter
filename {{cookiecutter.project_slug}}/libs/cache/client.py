from collections.abc import Callable

from django_redis.client import DefaultClient as BaseDefaultClient
from loguru import logger
from redis import Redis
from redis.exceptions import RedisError


class EnhancedRedisClient(BaseDefaultClient):
    def _get_client(self, write: bool = True) -> Redis:
        return self.get_client(write)

    def _make_key(self, key: str, version: int | None = None) -> str:
        return self.make_key(key, version=version)

    def _safe_decode(self, value):
        if hasattr(self, "decode") and callable(self.decode):
            return self.decode(value)
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return value

    def sadd(self, name: str, *values, version: int | None = None) -> int:
        try:
            client = self._get_client(write=True)
            key = self._make_key(name, version=version)
            return client.sadd(key, *values)
        except RedisError as e:
            logger.error(f"Redis sadd error for key {name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in sadd: {e}")
            raise

    def sismember(self, name: str, value: str, version: int | None = None) -> bool:
        client = self._get_client(write=False)
        key = self._make_key(name, version=version)
        return client.sismember(key, value)

    def smembers(self, name: str, version: int | None = None) -> set:
        client = self._get_client(write=False)
        key = self._make_key(name, version=version)
        return client.smembers(key)

    def srem(self, name: str, *values, version: int | None = None) -> int:
        client = self._get_client(write=True)
        key = self._make_key(name, version=version)
        return client.srem(key, *values)

    def zadd(
        self,
        name: str,
        mapping: dict,
        version: int | None = None,
        nx: bool = False,
        xx: bool = False,
        ch: bool = False,
        incr: bool = False,
        gt: bool = False,
        lt: bool = False,
    ) -> int | float:
        try:
            client = self._get_client(write=True)
            key = self._make_key(name, version=version)
            return client.zadd(key, mapping, nx=nx, xx=xx, ch=ch, incr=incr, gt=gt, lt=lt)
        except RedisError as e:
            logger.error(f"Redis zadd error for key {name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in zadd: {e}")
            raise

    def zincrby(
        self, name: str, amount: float, value: str, version: int | None = None
    ) -> float:
        client = self._get_client(write=True)
        key = self._make_key(name, version=version)
        return client.zincrby(key, amount, value)

    def zscore(self, name: str, value: str, version: int | None = None) -> float | None:
        client = self._get_client(write=False)
        key = self._make_key(name, version=version)
        return client.zscore(key, value)

    def zrank(
        self, name: str, value: str, withscore: bool = False, version: int | None = None
    ) -> int | tuple | None:
        client = self._get_client(write=False)
        key = self._make_key(name, version=version)
        return client.zrank(key, value, withscore=withscore)

    def zrevrank(
        self, name: str, value: str, withscore: bool = False, version: int | None = None
    ) -> int | tuple | None:
        client = self._get_client(write=False)
        key = self._make_key(name, version=version)
        return client.zrevrank(key, value, withscore=withscore)

    def zrange(
        self,
        name: str,
        start: int,
        end: int,
        version: int | None = None,
        desc: bool = False,
        withscores: bool = False,
        score_cast_func: type | Callable = float,
        byscore: bool = False,
        bylex: bool = False,
        offset: int | None = None,
        num: int | None = None,
    ) -> list:
        client = self._get_client(write=False)
        key = self._make_key(name, version=version)

        result = client.zrange(
            key,
            start,
            end,
            desc=desc,
            withscores=withscores,
            score_cast_func=score_cast_func,
            byscore=byscore,
            bylex=bylex,
            offset=offset,
            num=num,
        )
        if withscores:
            return [(self._safe_decode(item[0]), item[1]) for item in result]
        return [self._safe_decode(item) for item in result]

    def zrevrange(
        self,
        name: str,
        start: int,
        end: int,
        version: int | None = None,
        withscores: bool = False,
        score_cast_func: type | Callable = float,
    ) -> list:
        client = self._get_client(write=False)
        key = self._make_key(name, version=version)
        result = client.zrevrange(
            key, start, end, withscores=withscores, score_cast_func=score_cast_func
        )
        if withscores:
            return [(self._safe_decode(item[0]), item[1]) for item in result]
        return [self._safe_decode(item) for item in result]

    def zrangebyscore(
        self,
        name: str,
        min,
        max,
        version: int | None = None,
        start: int | None = None,
        num: int | None = None,
        withscores: bool = False,
        score_cast_func: type | Callable = float,
    ) -> list:
        client = self._get_client(write=False)
        key = self._make_key(name, version=version)

        result = client.zrangebyscore(
            key, min, max, start=start, num=num, withscores=withscores, score_cast_func=score_cast_func
        )
        if withscores:
            return [(self._safe_decode(item[0]), item[1]) for item in result]
        return [self._safe_decode(item) for item in result]

    def zcard(self, name: str, version: int | None = None) -> int:
        client = self._get_client(write=False)
        key = self._make_key(name, version=version)
        return client.zcard(key)

    def zrem(self, name: str, *values, version: int | None = None) -> int:
        client = self._get_client(write=True)
        key = self._make_key(name, version=version)
        return client.zrem(key, *values)

    def hset(self, name: str, key: str, value: str, version: int | None = None) -> int:
        client = self._get_client(write=True)
        cache_key = self._make_key(name, version=version)
        return client.hset(cache_key, key, value)

    def hget(self, name: str, key: str, version: int | None = None) -> str | None:
        client = self._get_client(write=False)
        cache_key = self._make_key(name, version=version)
        result = client.hget(cache_key, key)
        return self._safe_decode(result) if result is not None else None

    def hmset(self, name: str, mapping: dict, version: int | None = None) -> bool:
        client = self._get_client(write=True)
        cache_key = self._make_key(name, version=version)
        return client.hmset(cache_key, mapping)

    def hmget(self, name: str, keys: list[str], version: int | None = None) -> list:
        client = self._get_client(write=False)
        cache_key = self._make_key(name, version=version)
        results = client.hmget(cache_key, keys)
        return [self._safe_decode(item) if item is not None else None for item in results]

    def hgetall(self, name: str, version: int | None = None) -> dict:
        client = self._get_client(write=False)
        cache_key = self._make_key(name, version=version)
        result = client.hgetall(cache_key)
        return {self._safe_decode(k): self._safe_decode(v) for k, v in result.items()}

    def hdel(self, name: str, *keys, version: int | None = None) -> int:
        client = self._get_client(write=True)
        cache_key = self._make_key(name, version=version)
        return client.hdel(cache_key, *keys)

    def hexists(self, name: str, key: str, version: int | None = None) -> bool:
        client = self._get_client(write=False)
        cache_key = self._make_key(name, version=version)
        return client.hexists(cache_key, key)

    def hkeys(self, name: str, version: int | None = None) -> list[str]:
        client = self._get_client(write=False)
        cache_key = self._make_key(name, version=version)
        return [self._safe_decode(key) for key in client.hkeys(cache_key)]

    def hvals(self, name: str, version: int | None = None) -> list:
        client = self._get_client(write=False)
        cache_key = self._make_key(name, version=version)
        return [self._safe_decode(val) for val in client.hvals(cache_key)]

    def hlen(self, name: str, version: int | None = None) -> int:
        client = self._get_client(write=False)
        cache_key = self._make_key(name, version=version)
        return client.hlen(cache_key)

    def hincrby(
        self, name: str, key: str, amount: int = 1, version: int | None = None
    ) -> int:
        client = self._get_client(write=True)
        cache_key = self._make_key(name, version=version)
        return client.hincrby(cache_key, key, amount)

    def hincrbyfloat(
        self, name: str, key: str, amount: float = 1.0, version: int | None = None
    ) -> float:
        client = self._get_client(write=True)
        cache_key = self._make_key(name, version=version)
        return client.hincrbyfloat(cache_key, key, amount)

    def lpush(self, name: str, *values, version: int | None = None) -> int:
        client = self._get_client(write=True)
        key = self._make_key(name, version=version)
        return client.lpush(key, *values)

    def rpush(self, name: str, *values, version: int | None = None) -> int:
        client = self._get_client(write=True)
        key = self._make_key(name, version=version)
        return client.rpush(key, *values)

    def lpop(self, name: str, version: int | None = None) -> str | None:
        client = self._get_client(write=True)
        key = self._make_key(name, version=version)
        result = client.lpop(key)
        return self._safe_decode(result) if result is not None else None

    def rpop(self, name: str, version: int | None = None) -> str | None:
        client = self._get_client(write=True)
        key = self._make_key(name, version=version)
        result = client.rpop(key)
        return self._safe_decode(result) if result is not None else None

    def lrange(
        self, name: str, start: int, end: int, version: int | None = None
    ) -> list:
        client = self._get_client(write=False)
        key = self._make_key(name, version=version)
        results = client.lrange(key, start, end)
        return [self._safe_decode(item) for item in results]

    def llen(self, name: str, version: int | None = None) -> int:
        client = self._get_client(write=False)
        key = self._make_key(name, version=version)
        return client.llen(key)

    def lindex(self, name: str, index: int, version: int | None = None) -> str | None:
        client = self._get_client(write=False)
        key = self._make_key(name, version=version)
        result = client.lindex(key, index)
        return self._safe_decode(result) if result is not None else None

    def lset(
        self, name: str, index: int, value: str, version: int | None = None
    ) -> bool:
        client = self._get_client(write=True)
        key = self._make_key(name, version=version)
        return client.lset(key, index, value)

    def lrem(
        self, name: str, count: int, value: str, version: int | None = None
    ) -> int:
        client = self._get_client(write=True)
        key = self._make_key(name, version=version)
        return client.lrem(key, count, value)

    def ltrim(
        self, name: str, start: int, end: int, version: int | None = None
    ) -> bool:
        client = self._get_client(write=True)
        key = self._make_key(name, version=version)
        return client.ltrim(key, start, end)

    def expire(self, key: str, timeout: int) -> bool:
        client = self._get_client(write=True)
        return client.expire(key, timeout)

    def ttl(self, key: str) -> int:
        client = self._get_client(write=False)
        return client.ttl(key)

    def persist(self, key: str) -> bool:
        client = self._get_client(write=True)
        return client.persist(key)

    def type(self, key: str) -> str:
        client = self._get_client(write=False)
        return client.type(key)
