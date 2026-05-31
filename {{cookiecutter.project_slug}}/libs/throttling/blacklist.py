import hashlib
import math
import time

from django.conf import settings
from django.core.cache import cache

_TOKEN_PREFIX = "throttle_bl:"
_IP_PREFIX = "throttle_ip_bl:"


def _token_key(raw_token: str) -> str:
    return _TOKEN_PREFIX + hashlib.sha256(raw_token.encode()).hexdigest()


def _ip_key(ip: str) -> str:
    return _IP_PREFIX + ip


def _remaining_ttl(expires_at: float) -> int | None:
    remaining = math.ceil(expires_at - time.time())
    return remaining if remaining > 0 else None


def _resolve_ttl(ttl: int | None) -> int | None:
    if ttl is None:
        ttl = getattr(settings, "THROTTLE_BLACKLIST_TTL", 30)
    return ttl if ttl > 0 else None


def blacklist_token(raw_token: str, ttl: int | None = None) -> None:
    ttl = _resolve_ttl(ttl)
    if ttl is None:
        return
    cache.set(_token_key(raw_token), time.time() + ttl, timeout=ttl)


def blacklist_ip(ip: str, ttl: int | None = None) -> None:
    ttl = _resolve_ttl(ttl)
    if ttl is None:
        return
    cache.set(_ip_key(ip), time.time() + ttl, timeout=ttl)


def get_token_cooldown(raw_token: str) -> int | None:
    expires_at = cache.get(_token_key(raw_token))
    if expires_at is None:
        return None
    return _remaining_ttl(expires_at)


def is_ip_blacklisted(ip: str) -> int | None:
    expires_at = cache.get(_ip_key(ip))
    if expires_at is None:
        return None
    return _remaining_ttl(expires_at)
