import requests
from django.utils.translation import gettext_lazy as _

from core.restframework.error_handler import BaseError


class ClientRequestError(BaseError):
    code = 4100
    message = _("internal client request error")


class ClientTimeoutError(ClientRequestError):
    code = 4101
    message = _("request timeout error")


class ClientConnectionError(ClientRequestError):
    code = 4102
    message = _("connection error")


class ClientResponseError(ClientRequestError):
    code = 4103
    message = _("invalid response error")

    def __init__(
        self,
        message: str | None = None,
        *,
        response: requests.Response | None = None,
    ) -> None:
        super().__init__(message)
        self.response = response
