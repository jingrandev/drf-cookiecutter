"""URL configuration for project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.renderers import OpenApiJsonRenderer
from drf_spectacular.renderers import OpenApiYamlRenderer
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    {%- if cookiecutter.use_redis == "yes" %}
    path("admin/dj-redis-panel/", include("dj_redis_panel.urls")),
    path("admin/dj-cache-panel/", include("dj_cache_panel.urls")),
    {%- endif %}
    {%- if cookiecutter.use_celery == "yes" %}
    path("admin/dj-celery-panel/", include("dj_celery_panel.urls")),
    {%- endif %}
    path("admin/dj-urls-panel/", include("dj_urls_panel.urls")),
    path("admin/dj-signals-panel/", include("dj_signals_panel.urls")),
    path("admin/dj-control-room/", include("dj_control_room.urls")),
    path("admin/", admin.site.urls),
    path("", include("apps.api.endpoints")),
]


# API Documentation URLs - only added if SHOW_API_DOCS is True
if settings.SHOW_API_DOCS:
    urlpatterns += [
        # API Schema
        path(
            "schema/",
            SpectacularAPIView.as_view(
                renderer_classes=[OpenApiJsonRenderer, OpenApiYamlRenderer]
            ),
            name="api-schema",
        ),
        # Swagger UI
        path(
            "docs/",
            SpectacularSwaggerView.as_view(url_name="api-schema"),
            name="api-docs",
        ),
        # ReDoc UI
        path(
            "redoc/",
            SpectacularRedocView.as_view(url_name="api-schema"),
            name="api-redoc",
        ),
    ]

# Debug Toolbar URLs - only added if DEBUG is True
if settings.DEBUG:
    import debug_toolbar
    
    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]

# Silk URLs - only added if DEBUG is True
if settings.DEBUG:
    urlpatterns += [
        path("silk/", include("silk.urls", namespace="silk")),
    ]