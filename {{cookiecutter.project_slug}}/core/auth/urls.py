from django.urls import include
from django.urls import path

from core.restframework.routers import URLForceHyphenRouter

from core.auth.endpoints import AuthViewSet
from core.auth.endpoints import UserViewSet

router = URLForceHyphenRouter()
router.register("users", UserViewSet)

urlpatterns = [
    path(
        "login/",
        AuthViewSet.as_view({"post": "login"}),
        name="auth-login",
    ),
    path(
        "refresh/",
        AuthViewSet.as_view({"post": "refresh"}),
        name="auth-refresh",
    ),
    path(
        "logout/",
        AuthViewSet.as_view({"post": "logout"}),
        name="auth-logout",
    ),
    path("", include(router.urls)),
]
