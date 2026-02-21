from typing import Any

from django.conf import settings
from django.http import HttpRequest
from rest_framework.response import Response


def get_cookie_options(request: HttpRequest = None) -> dict[str, Any]:
    secure = getattr(settings, "AUTH_COOKIE_SECURE", not settings.DEBUG)
    samesite = getattr(settings, "AUTH_COOKIE_SAMESITE", "Lax")
    domain = getattr(settings, "AUTH_COOKIE_DOMAIN", None)
    httponly = getattr(settings, "AUTH_COOKIE_HTTPONLY", True)

    return {
        "httponly": httponly,
        "secure": secure,
        "samesite": samesite,
        "domain": domain,
    }


def set_auth_cookies(
    request: HttpRequest,
    response: Response,
    *,
    access: str,
    refresh: str,
) -> None:
    cookie_options = get_cookie_options(request)
    access_name = getattr(settings, "AUTH_COOKIE_ACCESS_NAME", "access")
    refresh_name = getattr(settings, "AUTH_COOKIE_REFRESH_NAME", "refresh")

    response.set_cookie(access_name, access, path="/", **cookie_options)
    response.set_cookie(refresh_name, refresh, path="/", **cookie_options)


def clear_auth_cookies(response: Response) -> None:
    cookie_options = get_cookie_options()
    delete_cookie_options = {
        "domain": cookie_options.get("domain"),
        "samesite": cookie_options.get("samesite"),
    }
    access_name = getattr(settings, "AUTH_COOKIE_ACCESS_NAME", "access")
    refresh_name = getattr(settings, "AUTH_COOKIE_REFRESH_NAME", "refresh")

    response.delete_cookie(access_name, path="/", **delete_cookie_options)
    response.delete_cookie(refresh_name, path="/", **delete_cookie_options)
