from dataclasses import dataclass

from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


@dataclass(frozen=True)
class LoginTokens:
    access: str
    refresh: str


@dataclass(frozen=True)
class LoginResult:
    user: object
    tokens: LoginTokens


def login_with_credentials(
    *,
    request,
    {%- if cookiecutter.username_type == "email" %}
    email: str,
    {%- else %}
    username: str,
    {%- endif %}
    password: str,
) -> LoginResult | None:
    auth_kwargs = {
        {%- if cookiecutter.username_type == "email" %}
        "email": email,
        {%- else %}
        "username": username,
        {%- endif %}
        "password": password,
    }
    user = authenticate(request, **auth_kwargs)
    if user is None:
        return None

    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    return LoginResult(user=user, tokens=LoginTokens(access=str(access), refresh=str(refresh)))


def refresh_with_refresh_token(*, refresh_token: str) -> LoginTokens:
    try:
        refresh = RefreshToken(refresh_token)
    except TokenError as exc:
        raise exc

    access = refresh.access_token
    return LoginTokens(access=str(access), refresh=str(refresh))
