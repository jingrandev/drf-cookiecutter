class RedisCommonMixin:
    def exists(self, key: str) -> bool:
        return self.has_key(key)  # noqa: DJ001

    def expire(self, key: str, timeout: int) -> bool:
        return self.client.expire(key, timeout)

    def ttl(self, key: str) -> int:
        return self.client.ttl(key)

    def persist(self, key: str) -> bool:
        return self.client.persist(key)

    def type(self, key: str) -> str:
        return self.client.type(key)


class RedisSetMixin:
    def sadd(self, name: str, *values, version: int | None = None) -> int:
        return self.client.sadd(name, *values, version=version)

    def sismember(self, name: str, value: str, version: int | None = None) -> bool:
        return self.client.sismember(name, value, version=version)

    def smembers(self, name: str, version: int | None = None) -> set:
        return self.client.smembers(name, version=version)

    def srem(self, name: str, *values, version: int | None = None) -> int:
        return self.client.srem(name, *values, version=version)


class RedisHashMixin:
    def hset(self, name: str, key: str, value: str, version: int | None = None) -> int:
        return self.client.hset(name, key, value, version=version)

    def hget(self, name: str, key: str, version: int | None = None) -> str | None:
        return self.client.hget(name, key, version=version)

    def hmset(self, name: str, mapping: dict, version: int | None = None) -> bool:
        return self.client.hmset(name, mapping, version=version)

    def hmget(self, name: str, keys: list[str], version: int | None = None) -> list:
        return self.client.hmget(name, keys, version=version)

    def hgetall(self, name: str, version: int | None = None) -> dict:
        return self.client.hgetall(name, version=version)

    def hdel(self, name: str, *keys, version: int | None = None) -> int:
        return self.client.hdel(name, *keys, version=version)

    def hexists(self, name: str, key: str, version: int | None = None) -> bool:
        return self.client.hexists(name, key, version=version)

    def hkeys(self, name: str, version: int | None = None) -> list[str]:
        return self.client.hkeys(name, version=version)

    def hvals(self, name: str, version: int | None = None) -> list:
        return self.client.hvals(name, version=version)

    def hlen(self, name: str, version: int | None = None) -> int:
        return self.client.hlen(name, version=version)

    def hincrby(
        self, name: str, key: str, amount: int = 1, version: int | None = None
    ) -> int:
        return self.client.hincrby(name, key, amount, version=version)

    def hincrbyfloat(
        self, name: str, key: str, amount: float = 1.0, version: int | None = None
    ) -> float:
        return self.client.hincrbyfloat(name, key, amount, version=version)


class RedisListMixin:
    def lpush(self, name: str, *values, version: int | None = None) -> int:
        return self.client.lpush(name, *values, version=version)

    def rpush(self, name: str, *values, version: int | None = None) -> int:
        return self.client.rpush(name, *values, version=version)

    def lpop(self, name: str, version: int | None = None) -> str | None:
        return self.client.lpop(name, version=version)

    def rpop(self, name: str, version: int | None = None) -> str | None:
        return self.client.rpop(name, version=version)

    def lrange(
        self, name: str, start: int, end: int, version: int | None = None
    ) -> list:
        return self.client.lrange(name, start, end, version=version)

    def llen(self, name: str, version: int | None = None) -> int:
        return self.client.llen(name, version=version)

    def lindex(self, name: str, index: int, version: int | None = None) -> str | None:
        return self.client.lindex(name, index, version=version)

    def lset(
        self, name: str, index: int, value: str, version: int | None = None
    ) -> bool:
        return self.client.lset(name, index, value, version=version)

    def lrem(
        self, name: str, count: int, value: str, version: int | None = None
    ) -> int:
        return self.client.lrem(name, count, value, version=version)

    def ltrim(
        self, name: str, start: int, end: int, version: int | None = None
    ) -> bool:
        return self.client.ltrim(name, start, end, version=version)


class RedisSortedSetMixin:
    def zadd(self, name: str, mapping: dict, version: int | None = None, **kwargs):
        return self.client.zadd(name, mapping, version=version, **kwargs)

    def zrange(
        self, name: str, start: int, end: int, version: int | None = None, **kwargs
    ):
        return self.client.zrange(name, start, end, version=version, **kwargs)

    def zrevrange(
        self, name: str, start: int, end: int, version: int | None = None, **kwargs
    ):
        return self.client.zrevrange(name, start, end, version=version, **kwargs)

    def zrangebyscore(self, name: str, min, max, version: int | None = None, **kwargs):
        return self.client.zrangebyscore(name, min, max, version=version, **kwargs)

    def zscore(self, name: str, value: str, version: int | None = None):
        return self.client.zscore(name, value, version=version)

    def zincrby(self, name: str, amount: float, value: str, version: int | None = None):
        return self.client.zincrby(name, amount, value, version=version)

    def zrank(self, name: str, value: str, version: int | None = None, **kwargs):
        return self.client.zrank(name, value, version=version, **kwargs)

    def zrevrank(self, name: str, value: str, version: int | None = None, **kwargs):
        return self.client.zrevrank(name, value, version=version, **kwargs)

    def zcard(self, name: str, version: int | None = None):
        return self.client.zcard(name, version=version)

    def zrem(self, name: str, *values, version: int | None = None):
        return self.client.zrem(name, *values, version=version)


class RedisLockMixin:
    def lock(
        self,
        name: str,
        timeout: float | None = None,
        sleep: float = 0.1,
        blocking: bool = True,
        blocking_timeout: float | None = None,
        thread_local: bool = True,
    ):
        from .lock import EnhancedLock

        client = self.client.get_client(write=True)
        key = self.make_key(name)

        return EnhancedLock(
            client,
            key,
            timeout=timeout,
            sleep=sleep,
            blocking=blocking,
            blocking_timeout=blocking_timeout,
            thread_local=thread_local,
        )
