import requests
from django.utils.translation import gettext_lazy as _

from core.restframework.error_handler import BaseError


class ClientRequestError(BaseError):
    code = "HC_1000"
    message = _("internal client request error")


class ClientTimeoutError(ClientRequestError):
    code = "HC_1001"
    message = _("request timeout error")


class ClientConnectionError(ClientRequestError):
    code = "HC_1002"
    message = _("connection error")


class ClientResponseError(ClientRequestError):
    code = "HC_1003"
    message = _("invalid response error")

    def __init__(
        self,
        message: str | None = None,
        *,
        response: requests.Response | None = None,
    ) -> None:
        super().__init__(message)
        self.response = response
