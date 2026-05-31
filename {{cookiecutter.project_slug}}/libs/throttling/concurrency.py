from django.conf import settings
from django.core.cache import cache
from loguru import logger
from rest_framework.throttling import SimpleRateThrottle

from libs.throttling.blacklist import blacklist_ip, blacklist_token
from libs.throttling.errors import ConcurrencyLimitExceeded
from libs.throttling.utils import get_auth_token, get_client_ip

_REQUEST_ATTR_KEY = "_concurrency_throttle_cache_key"

_CONCURRENT_CACHE_PREFIX = "concurrent_req:"


class ConcurrentUserRequestsThrottle(SimpleRateThrottle):
    """Limits concurrent requests per user (or IP for anonymous).

    Unlike standard rate throttling which counts requests over a time window,
    this counts how many requests are **in-flight** right now.

    Usage (per-view, with custom limit)::

        class ExportViewSet(ViewSet):
            throttle_classes = [ConcurrentUserRequestsThrottle]
            concurrent_request_limit = 3   # override per view

    The default limit is read from ``settings.CONCURRENT_REQUESTS_PER_USER``.
    If the view does not set ``concurrent_request_limit``, the setting is used.
    If neither exists, the class ``rate`` attribute (``num_requests/duration``)
    is used as a fallback.

    When the limit is exceeded the token/IP is optionally added to a short-lived
    blacklist (see ``ThrottleBlacklistMiddleware``) so subsequent requests are
    rejected before reaching DRF.
    """

    scope = "concurrent_user_requests"

    def get_cache_key(self, request, view=None):
        user = request.user
        if hasattr(user, "is_authenticated") and user.is_authenticated:
            if getattr(user, "is_staff", False):
                return None
            ident = str(user.id)
        elif getattr(settings, "THROTTLE_IP_ENABLED", True):
            ident = get_client_ip(request)
        else:
            return None
        return f"{_CONCURRENT_CACHE_PREFIX}{ident}"

    def _get_limit(self, view) -> int:
        limit = getattr(view, "concurrent_request_limit", None)
        if limit is not None:
            return int(limit)
        return getattr(settings, "CONCURRENT_REQUESTS_PER_USER", 10)

    def _get_timeout(self) -> int:
        return getattr(settings, "CONCURRENT_REQUESTS_TIMEOUT", 60)

    def allow_request(self, request, view):
        limit = self._get_limit(view)
        if limit <= 0:
            return True

        cache_key = self.get_cache_key(request, view)
        if cache_key is None:
            return True

        try:
            current = cache.incr(cache_key)
        except ValueError:
            current = cache.get_or_set(cache_key, 1, timeout=self._get_timeout())
            if current != 1:
                try:
                    current = cache.incr(cache_key)
                except ValueError:
                    current = 1

        if current == 1:
            cache.expire(cache_key, self._get_timeout())

        if current > limit:
            try:
                cache.decr(cache_key)
            except ValueError:
                pass
            self._deny(request, current, limit)
            return False

        django_request = getattr(request, "_request", request)
        setattr(django_request, _REQUEST_ATTR_KEY, cache_key)
        logger.debug(
            "throttle:ALLOW path={} key={} count={}/{}",
            request.path,
            cache_key,
            current,
            limit,
        )
        return True

    def _deny(self, request, count, limit):
        cooldown = getattr(settings, "THROTTLE_BLACKLIST_TTL", 30)
        if cooldown > 0:
            self._blacklist(request, ttl=cooldown)
        else:
            cooldown = None

        logger.warning(
            "throttle:DENY path={} count={}/{} cooldown={}s",
            request.path,
            count,
            limit,
            cooldown,
        )
        raise ConcurrencyLimitExceeded(
            message=f"Concurrent request limit ({limit}) exceeded. Retry after {cooldown}s."
            if cooldown
            else f"Concurrent request limit ({limit}) exceeded."
        )

    @staticmethod
    def _blacklist(request, ttl: int | None = None) -> None:
        token = get_auth_token(request)
        if token:
            blacklist_token(token, ttl=ttl)
        else:
            blacklist_ip(get_client_ip(request), ttl=ttl)

    @staticmethod
    def on_request_processed(request) -> None:
        django_request = getattr(request, "_request", request)
        cache_key = getattr(django_request, _REQUEST_ATTR_KEY, None)
        if not cache_key:
            return
        try:
            cache.decr(cache_key)
            logger.debug("throttle:RELEASE key={}", cache_key)
        except ValueError:
            logger.debug("throttle:RELEASE key={} already expired", cache_key)
