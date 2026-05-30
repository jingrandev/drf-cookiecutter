from rest_framework import status

from core.restframework.error_handler import BaseError


class ConcurrencyLimitExceeded(BaseError):
    code = "RATE_1002"
    message = "Concurrent request limit exceeded."
    http_status = status.HTTP_429_TOO_MANY_REQUESTS
