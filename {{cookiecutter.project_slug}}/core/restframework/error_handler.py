from typing import Any

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from loguru import logger
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.exceptions import NotAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import Throttled
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

error_registry: dict[int | str, type] = {}


class BaseError(Exception):
    """Base class for API errors.

    This class serves as a base for all API-specific exceptions. Do not use this class directly;
    instead, create a subclass for each specific error type.

    Attributes:
        code (int | str): Error code. Reserved codes (1-19) are for system use.
            Subclass codes should start from 20 and increment.
        message (str): Default error message.
        http_status (int): HTTP status code for the error.

    Note:
        - Each specific error type that needs to be handled by the frontend should have its own subclass
          with a unique error code.
        - For request parameter validation errors, use HTTP 400 responses directly instead of this class.
        - The error registry ensures unique error codes across all subclasses.
    """

    code: int | str = 1
    message: str = _("API Internal Error")
    http_status: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str | None = None) -> None:
        """Initialize the error with an optional custom message.

        Args:
            message: Custom error message. If None, uses the class default message.
        """
        super().__init__(message or self.message)
        self.message = message or self.message

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Register subclass error codes in the global registry.

        Raises:
            ValueError: If the error code is already registered.
        """
        if cls.code in error_registry:
            error_msg = f"Error code {cls.code} is already registered by {error_registry[cls.code].__name__}"
            raise ValueError(error_msg)
        error_registry[cls.code] = cls
        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return self.message

    def get_response_data(self) -> dict[str, list[dict[str, Any]]]:
        """Get the error response data in a standardized format.

        Returns:
            A dictionary containing the error code and message in the standard format.
        """
        return {"errors": [{"code": self.code, "message": self.message}]}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(code={self.code}, message={self.message!r})>"


def _build_error_response(
    *, code: str, message: str, data: dict[str, Any] | None, http_status: int
) -> Response:
    return Response(
        {
            "code": code,
            "data": data or {},
            "message": message,
        },
        status=http_status,
    )


def handle_exception(exc: Exception, context: dict[str, Any]) -> Response | None:
    if isinstance(exc, BaseError):
        return _build_error_response(
            code=str(exc.code),
            message=str(exc.message),
            data={},
            http_status=getattr(exc, "http_status", status.HTTP_400_BAD_REQUEST),
        )

    from rest_framework.views import exception_handler as drf_exception_handler

    drf_response = drf_exception_handler(exc, context)
    if drf_response is None:
        if getattr(settings, "PROPAGATE_API_EXCEPTIONS", False):
            return None

        logger.opt(exception=exc).error("Unhandled exception converted to SYS_5000")
        return _build_error_response(
            code="SYS_5000",
            message="internal error",
            data={},
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    http_status = drf_response.status_code
    raw_data: Any = drf_response.data

    if isinstance(exc, ValidationError):
        return _build_error_response(
            code="REQ_1001",
            message="validation error",
            data={"errors": raw_data},
            http_status=http_status,
        )

    if isinstance(exc, NotAuthenticated):
        message = "not authenticated"
        if isinstance(raw_data, dict) and "detail" in raw_data:
            message = str(raw_data.get("detail"))
        return _build_error_response(
            code="AUTH_1000",
            message=message,
            data={"errors": raw_data} if raw_data else {},
            http_status=http_status,
        )

    if isinstance(exc, AuthenticationFailed):
        message = "authentication failed"
        if isinstance(raw_data, dict) and "detail" in raw_data:
            message = str(raw_data.get("detail"))
        return _build_error_response(
            code="AUTH_1002",
            message=message,
            data={"errors": raw_data} if raw_data else {},
            http_status=http_status,
        )

    if isinstance(exc, PermissionDenied):
        message = "permission denied"
        if isinstance(raw_data, dict) and "detail" in raw_data:
            message = str(raw_data.get("detail"))
        return _build_error_response(
            code="PERM_1001",
            message=message,
            data={"errors": raw_data} if raw_data else {},
            http_status=http_status,
        )

    if isinstance(exc, Throttled):
        message = "rate limited"
        if isinstance(raw_data, dict) and "detail" in raw_data:
            message = str(raw_data.get("detail"))
        return _build_error_response(
            code="RATE_1001",
            message=message,
            data={"errors": raw_data} if raw_data else {},
            http_status=http_status,
        )

    if isinstance(exc, APIException):
        message = "error"
        if isinstance(raw_data, dict) and "detail" in raw_data:
            message = str(raw_data.get("detail"))
        return _build_error_response(
            code="REQ_1000" if 400 <= http_status < 500 else "SYS_5000",
            message=message,
            data={"errors": raw_data} if raw_data else {},
            http_status=http_status,
        )

    return _build_error_response(
        code="SYS_5000",
        message="internal error",
        data={"errors": raw_data} if raw_data else {},
        http_status=http_status,
    )
