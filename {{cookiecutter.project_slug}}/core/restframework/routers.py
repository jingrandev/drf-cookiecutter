from django.conf import settings
from rest_framework.routers import DefaultRouter
from rest_framework.routers import Route
from rest_framework.routers import SimpleRouter
from rest_framework.routers import escape_curly_brackets
from rest_framework_nested.routers import NestedDefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter


def get_router_class():
    return DefaultRouter if settings.DEBUG else SimpleRouter


def get_router():
    return get_router_class()()


BaseRouter = get_router_class()


def get_nested_router_class():
    return NestedDefaultRouter if BaseRouter is DefaultRouter else NestedSimpleRouter


def get_nested_router(*args, **kwargs):
    return get_nested_router_class()(*args, **kwargs)


class URLForceHyphenRouter(BaseRouter):
    """Router forcing action url_path to use hyphenated segments."""

    def _get_dynamic_route(self, route, action):
        initkwargs = route.initkwargs.copy()
        initkwargs.update(action.kwargs)

        url_path = escape_curly_brackets(action.url_path)
        url_path = url_path.replace("_", "-")

        return Route(
            url=route.url.replace("{url_path}", url_path),
            mapping=action.mapping,
            name=route.name.replace("{url_name}", action.url_name),
            detail=route.detail,
            initkwargs=initkwargs,
        )
