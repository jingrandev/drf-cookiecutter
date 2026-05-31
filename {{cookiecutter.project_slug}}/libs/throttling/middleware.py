from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse

from libs.throttling.blacklist import get_token_cooldown, is_ip_blacklisted
from libs.throttling.concurrency import ConcurrentUserRequestsThrottle
from libs.throttling.utils import get_auth_token, get_client_ip


class ThrottleBlacklistMiddleware:
    """Fast-path rejection for recently throttled tokens and IPs.

    When ``ConcurrentUserRequestsThrottle`` denies a request it writes the
    bearer token's SHA-256 hash (or client IP) to the cache with a short TTL.
    This middleware checks that blacklist **before** authentication so that
    repeat offenders are rejected with zero DB/DRF overhead.

    Placed *before* ``AuthenticationMiddleware`` in ``MIDDLEWARE``.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        token = get_auth_token(request)
        if token:
            cooldown = get_token_cooldown(token)
        elif getattr(settings, "THROTTLE_IP_ENABLED", True):
            cooldown = is_ip_blacklisted(get_client_ip(request))
        else:
            cooldown = None

        if cooldown is not None:
            response = JsonResponse(
                {
                    "code": "RATE_1002",
                    "data": {},
                    "message": "Too many requests. Please retry later.",
                },
                status=429,
            )
            response["Retry-After"] = str(cooldown)
            return response

        return self.get_response(request)


class ConcurrentRequestsMiddleware:
    """Decrements the concurrency counter after a response is generated.

    Pairs with ``ConcurrentUserRequestsThrottle``.  Must be placed **after**
    all views/middleware so that ``finally`` runs last.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        try:
            return self.get_response(request)
        finally:
            ConcurrentUserRequestsThrottle.on_request_processed(request)
