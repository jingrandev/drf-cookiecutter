from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core.auth.serializers.auth import LoginRequestSerializer
from core.auth.serializers.auth import LogoutResponseSerializer
from core.auth.serializers.auth import RefreshResponseSerializer
from core.auth.serializers.user import UserSerializer
from core.auth.services import auth_cookies
from core.auth.services import auth_service
from core.restframework.error_handler import BaseError


class InvalidCredentialsError(BaseError):
    code = "AUTH_1001"
    message = "invalid credentials"
    http_status = status.HTTP_401_UNAUTHORIZED


class RefreshFailedError(BaseError):
    code = "AUTH_1003"
    message = "session expired"
    http_status = status.HTTP_401_UNAUTHORIZED


class AuthViewSet(GenericViewSet):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        operation_id="auth_login",
        request=LoginRequestSerializer,
        responses={status.HTTP_200_OK: UserSerializer},
        tags=["auth"],
    )
    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request, *args, **kwargs):
        serializer = LoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        {%- if cookiecutter.username_type == "email" %}
        email = serializer.validated_data.get("email")
        {%- else %}
        username = serializer.validated_data.get("username")
        {%- endif %}
        password = serializer.validated_data["password"]

        login_result = auth_service.login_with_credentials(
            request=request,
            {%- if cookiecutter.username_type == "email" %}
            email=str(email),
            {%- else %}
            username=str(username),
            {%- endif %}
            password=str(password),
        )
        if login_result is None:
            raise InvalidCredentialsError()

        response = Response(UserSerializer(login_result.user).data, status=status.HTTP_200_OK)
        auth_cookies.set_auth_cookies(
            request=request,
            response=response,
            access=login_result.tokens.access,
            refresh=login_result.tokens.refresh,
        )
        return response

    @extend_schema(
        operation_id="auth_refresh",
        request=None,
        responses={status.HTTP_200_OK: RefreshResponseSerializer},
        tags=["auth"],
    )
    @action(detail=False, methods=["post"], url_path="refresh")
    def refresh(self, request, *args, **kwargs):
        refresh_cookie_name = getattr(settings, "AUTH_COOKIE_REFRESH_NAME", "refresh")
        refresh_token = request.COOKIES.get(refresh_cookie_name)
        if not refresh_token:
            raise RefreshFailedError()

        try:
            tokens = auth_service.refresh_with_refresh_token(refresh_token=refresh_token)
        except Exception as err:
            raise RefreshFailedError() from err

        response_serializer = RefreshResponseSerializer(data={"success": True})
        response_serializer.is_valid(raise_exception=True)

        response = Response(response_serializer.data, status=status.HTTP_200_OK)
        auth_cookies.set_auth_cookies(
            request=request,
            response=response,
            access=tokens.access,
            refresh=tokens.refresh,
        )
        return response

    @extend_schema(
        operation_id="auth_logout",
        request=None,
        responses={status.HTTP_200_OK: LogoutResponseSerializer},
        tags=["auth"],
    )
    @action(detail=False, methods=["post"], url_path="logout")
    def logout(self, request, *args, **kwargs):
        response_serializer = LogoutResponseSerializer(data={"success": True})
        response_serializer.is_valid(raise_exception=True)

        response = Response(response_serializer.data, status=status.HTTP_200_OK)
        auth_cookies.clear_auth_cookies(response)
        return response
