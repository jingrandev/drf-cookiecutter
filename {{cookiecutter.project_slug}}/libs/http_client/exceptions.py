from django.utils.translation import gettext_lazy as _

from core.restframework.error_handler import BaseError


class ClientRequestError(BaseError):
    """Base exception for all client request errors"""

    code = 4100
    message = _("internal client request error")


class ClientTimeoutError(ClientRequestError):
    """Raised when a request times out"""

    code = 4101
    message = _("request timeout error")


class ClientConnectionError(ClientRequestError):
    """Raised when connection fails"""

    code = 4102
    message = _("connection error")


class ClientResponseError(ClientRequestError):
    """Raised when receiving an invalid response"""

    code = 4103
    message = _("invalid response error")
