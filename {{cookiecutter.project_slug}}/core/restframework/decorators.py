from functools import wraps
from typing import Any
from typing import Type

from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class RequestBodyValidationException(ValidationError):
    """Raised when request body validation fails via ``@validate_body``."""

    def __init__(self, detail: Any = None, code: str | None = None) -> None:
        super().__init__(detail, code=code)


class QueryParameterValidationException(ValidationError):
    """Raised when query parameter validation fails via ``@validate_query_parameters``."""

    def __init__(self, detail: Any = None, code: str | None = None) -> None:
        super().__init__(detail, code=code)


def _get_request(args: tuple) -> Any:
    """Extract the request object from view method args (self, request, ...)."""
    for arg in args[1:]:
        if hasattr(arg, "data"):
            return arg
    raise ValueError("Could not find request object in view arguments.")


def validate_body(
    serializer_class: Type[serializers.Serializer],
    *,
    partial: bool = False,
    return_validated: bool = False,
):
    """Decorator that validates request body with a serializer.

    The validated data is injected into the wrapped method's ``kwargs["data"]``.

    Usage::

        @validate_body(CreateItemSerializer)
        def post(self, request, data):
            item = ItemService.create(**data)
            ...

        @validate_body(UpdateItemSerializer, partial=True, return_validated=True)
        def patch(self, request, data):
            ...

    Raises:
        RequestBodyValidationException: On validation failure (mapped to REQ_1001
            by the existing ``ExceptionHandler``).
        ValueError: If ``data`` key already exists in kwargs.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if "data" in kwargs:
                raise ValueError("'data' is already present in kwargs.")

            request = _get_request(args)
            serializer = serializer_class(
                data=request.data, partial=partial, context={"request": request}
            )
            if not serializer.is_valid():
                raise RequestBodyValidationException(detail=serializer.errors)

            kwargs["data"] = (
                serializer.validated_data if return_validated else serializer.data
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_query_parameters(
    serializer_class: Type[serializers.Serializer],
    *,
    return_validated: bool = False,
):
    """Decorator that validates query parameters with a serializer.

    The validated params are injected into ``kwargs["query_params"]``.

    Usage::

        class ListItemsQueryParams(serializers.Serializer):
            status = serializers.CharField(required=False)
            page = serializers.IntegerField(required=False, default=1)

        @validate_query_parameters(ListItemsQueryParams)
        def get(self, request, query_params):
            ...

    Raises:
        QueryParameterValidationException: On validation failure.
        ValueError: If ``query_params`` key already exists in kwargs.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if "query_params" in kwargs:
                raise ValueError("'query_params' is already present in kwargs.")

            request = _get_request(args)
            params = request.query_params.dict()
            serializer = serializer_class(data=params)
            if not serializer.is_valid():
                raise QueryParameterValidationException(detail=serializer.errors)

            kwargs["query_params"] = (
                serializer.validated_data if return_validated else serializer.data
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator
