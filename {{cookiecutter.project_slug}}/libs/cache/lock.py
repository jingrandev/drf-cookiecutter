from collections.abc import Iterator
from contextlib import contextmanager

from redis.exceptions import LockError
from redis.exceptions import ResponseError
from redis.lock import Lock as BaseLock


class EnhancedLock(BaseLock):
    @contextmanager
    def guard(
        self,
        *,
        blocking: bool | None = None,
        blocking_timeout: float | None = None,
    ) -> Iterator[bool]:
        acquired = self.acquire(
            blocking=self.blocking if blocking is None else blocking,
            blocking_timeout=blocking_timeout,
        )
        try:
            yield bool(acquired)
        finally:
            if acquired:
                self.release_ignore_exc()

    def release_ignore_exc(self) -> bool:
        try:
            self.release()
            return True
        except LockError:
            return False
        except ResponseError:
            return False
