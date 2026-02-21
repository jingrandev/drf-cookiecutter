from dataclasses import dataclass
from typing import Any
from typing import Callable
from typing import ClassVar

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

CodeResolver = Callable[[int], str]
LogHook = Callable[[Exception, dict[str, Any], str], None]
ExtraDataHook = Callable[[Exception, dict[str, Any], dict[str, Any]], dict[str, Any]]
ResponseBuilder = Callable[
    [Exception, dict[str, Any], Any, int | None], Response
]


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


@dataclass(frozen=True)
class HandlerRule:
    code: str | None
    default_message: str = "error"
    include_errors: bool = False
    code_resolver: CodeResolver | None = None
    log_hook: LogHook | None = None
    extra_data_hook: ExtraDataHook | None = None
    requires_drf_response: bool = True
    response_builder: ResponseBuilder | None = None

    def build(
        self,
        exc: Exception,
        context: dict[str, Any],
        raw_data: Any,
        http_status: int | None,
    ) -> Response:
        status_code = http_status or status.HTTP_500_INTERNAL_SERVER_ERROR
        if self.response_builder is not None:
            response = self.response_builder(exc, context, raw_data, status_code)
            if self.log_hook:
                self.log_hook(exc, context, self._resolve_code(status_code))
            return response

        message = ExceptionHandler.extract_detail_message(
            raw_data, default=self.default_message
        )
        code = self._resolve_code(status_code)
        errors = ExceptionHandler.normalize_errors(raw_data)
        body: dict[str, Any] = {}
        if self.include_errors or raw_data:
            body["errors"] = errors
        if self.extra_data_hook:
            try:
                body = self.extra_data_hook(exc, context, body) or body
            except Exception:
                pass
        if self.log_hook:
            self.log_hook(exc, context, code)
        return ExceptionHandler._build_response(
            code=code,
            message=message,
            data=body,
            http_status=status_code,
        )

    def _resolve_code(self, status_code: int) -> str:
        if self.code_resolver is not None:
            return self.code_resolver(status_code)
        if self.code is None:
            return "SYS_5000"
        return self.code


class ExceptionHandler:
    rules: ClassVar[list[tuple[type[Exception], HandlerRule]]] = []
    default_rule: ClassVar[HandlerRule | None] = None

    @staticmethod
    def _build_response(
        *, code: str, message: str, data: dict[str, Any] | None, http_status: int
    ) -> Response:
        return Response(
            {
                "code": code,
                "message": message,
                "data": data or {},
            },
            status=http_status,
        )

    @classmethod
    def register(
        cls,
        exc_type: type[Exception],
        *,
        code: str | None,
        default_message: str,
        include_errors: bool = False,
        code_resolver: CodeResolver | None = None,
        log_hook: LogHook | None = None,
        extra_data_hook: ExtraDataHook | None = None,
        requires_drf_response: bool = True,
        response_builder: ResponseBuilder | None = None,
    ) -> None:
        rule = HandlerRule(
            code=code,
            default_message=default_message,
            include_errors=include_errors,
            code_resolver=code_resolver,
            log_hook=log_hook,
            extra_data_hook=extra_data_hook,
            requires_drf_response=requires_drf_response,
            response_builder=response_builder,
        )
        cls.rules.append((exc_type, rule))
        if exc_type is Exception:
            cls.default_rule = rule

    @classmethod
    def resolve(cls, exc: Exception) -> HandlerRule | None:
        for exc_type, rule in cls.rules:
            if isinstance(exc, exc_type):
                return rule
        return None

    @classmethod
    def resolve_default(cls) -> HandlerRule:
        if cls.default_rule is None:
            cls.default_rule = HandlerRule(
                code="SYS_5000",
                default_message="internal error",
                include_errors=True,
                log_hook=cls.log_unhandled_exception,
            )
        return cls.default_rule

    @staticmethod
    def get_detail(raw_data: Any) -> str | None:
        if isinstance(raw_data, dict) and "detail" in raw_data:
            try:
                return str(raw_data.get("detail"))
            except Exception:
                return None
        return None

    @classmethod
    def extract_detail_message(cls, raw_data: Any, *, default: str) -> str:
        detail = cls.get_detail(raw_data)
        return default if detail is None else detail

    @staticmethod
    def normalize_errors(raw_data: Any) -> Any:
        if raw_data is None:
            return {}
        if isinstance(raw_data, (dict, list)):
            return raw_data
        return {"detail": raw_data}

    @staticmethod
    def log_unhandled_exception(
        exc: Exception, context: dict[str, Any], code: str
    ) -> None:
        logger.opt(exception=exc).error("Unhandled exception converted to %s", code)

    @staticmethod
    def build_base_error_response(
        exc: Exception,
        context: dict[str, Any],
        raw_data: Any,
        http_status: int | None,
    ) -> Response:
        assert isinstance(exc, BaseError)
        return ExceptionHandler._build_response(
            code=str(exc.code),
            message=str(exc.message),
            data=exc.get_response_data(),
            http_status=getattr(exc, "http_status", status.HTTP_400_BAD_REQUEST),
        )


ExceptionHandler.register(
    BaseError,
    code=None,
    default_message="base error",
    requires_drf_response=False,
    response_builder=ExceptionHandler.build_base_error_response,
)

ExceptionHandler.register(
    ValidationError,
    code="REQ_1001",
    default_message="validation error",
    include_errors=True,
)

ExceptionHandler.register(
    NotAuthenticated,
    code="AUTH_1000",
    default_message="not authenticated",
    include_errors=True,
)

ExceptionHandler.register(
    AuthenticationFailed,
    code="AUTH_1002",
    default_message="authentication failed",
    include_errors=True,
)

ExceptionHandler.register(
    PermissionDenied,
    code="PERM_1001",
    default_message="permission denied",
    include_errors=True,
)

ExceptionHandler.register(
    Throttled,
    code="RATE_1001",
    default_message="rate limited",
    include_errors=True,
)

ExceptionHandler.register(
    APIException,
    code=None,
    default_message="error",
    include_errors=True,
    code_resolver=lambda status_code: "REQ_1000"
    if 400 <= status_code < 500
    else "SYS_5000",
)

ExceptionHandler.register(
    Exception,
    code="SYS_5000",
    default_message="internal error",
    include_errors=True,
    log_hook=ExceptionHandler.log_unhandled_exception,
)
def handle_exception(exc: Exception, context: dict[str, Any]) -> Response | None:
    rule = ExceptionHandler.resolve(exc)
    if rule and not rule.requires_drf_response:
        return rule.build(exc, context, raw_data=None, http_status=None)

    from rest_framework.views import exception_handler as drf_exception_handler

    drf_response = drf_exception_handler(exc, context)
    if drf_response is None:
        if getattr(settings, "PROPAGATE_API_EXCEPTIONS", False):
            return None
        fallback_rule = rule or ExceptionHandler.resolve_default()
        return fallback_rule.build(
            exc,
            context,
            raw_data=None,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    http_status = drf_response.status_code
    raw_data: Any = getattr(drf_response, "data", {})
    rule = rule or ExceptionHandler.resolve(exc) or ExceptionHandler.resolve_default()
    return rule.build(exc, context, raw_data=raw_data, http_status=http_status)
