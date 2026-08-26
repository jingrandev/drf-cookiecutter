# ruff: noqa: ERA001, E501
"""Base settings to build other settings files upon."""

from pathlib import Path

import environ
from datetime import timedelta
from unfold.contrib.constance.settings import UNFOLD_CONSTANCE_ADDITIONAL_FIELDS
{%- if cookiecutter.use_celery == "yes" %}

from django_guid.integrations import CeleryIntegration
{%- endif %}

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=False)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(BASE_DIR / ".env"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="django-insecure-change-this-in-production",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = []

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "unfold",
    "unfold.contrib.constance",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]
THIRD_PARTY_APPS = [
    "libs.extensions",
    "django_extensions",
    "rest_framework",
    "rest_framework_simplejwt",
    "djoser",
    "drf_spectacular",
    "simple_history",
    "constance",
    "waffle",
    "django_guid",
    {%- if cookiecutter.use_celery == "yes" %}
    "django_celery_beat",
    "django_celery_results",
    {%- endif %}
    {%- if cookiecutter.use_auditlog == "yes" %}
    "auditlog",
    {%- endif %}
    "dj_control_room_base",
    {%- if cookiecutter.use_redis == "yes" %}
    "dj_redis_panel",
    "dj_cache_panel",
    {%- endif %}
    {%- if cookiecutter.use_celery == "yes" %}
    "dj_celery_panel",
    {%- endif %}
    "dj_urls_panel",
    "dj_signals_panel",
    "dj_control_room",
]
LOCAL_APPS = [
    "core.auth",
    "core.admin",
    "libs.di",
    "apps.api",
    "libs.logging",
    {%- if cookiecutter.use_redis == "yes" %}
    "libs.cache",
    {%- endif %}
    {%- if cookiecutter.use_celery == "yes" %}
    "libs.mq",
    {%- endif %}
    {%- if cookiecutter.use_email == "yes" %}
    "libs.email",
    {%- endif %}
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = "authentication.User"

MIDDLEWARE = [
    "django_guid.middleware.guid_middleware",
    "django.middleware.security.SecurityMiddleware",
    "core.restframework.middleware.UnifiedAPIExceptionMiddleware",
    {%- if cookiecutter.use_redis == "yes" %}
    "libs.throttling.middleware.ThrottleBlacklistMiddleware",
    {%- endif %}
    "django.contrib.sessions.middleware.SessionMiddleware",
    "core.admin.middleware.AdminGateMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "waffle.middleware.WaffleMiddleware",
    {%- if cookiecutter.use_auditlog == "yes" %}
    "auditlog.middleware.AuditlogMiddleware",
    {%- endif %}
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    {%- if cookiecutter.use_redis == "yes" %}
    "libs.throttling.middleware.ConcurrentRequestsMiddleware",
    {%- endif %}
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "constance.context_processors.config",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# DATABASE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR}/db.sqlite3",
    )
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True

# https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-DEFAULT_AUTO_FIELD
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/dev/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework
# ------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "core.restframework.renderers.StandardResponseRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "core.auth.authentication.CookieJWTAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "core.restframework.pagination.BasePageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.restframework.error_handler.handle_exception",
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
}

# API Documentation
# ------------------------------------------------------------------------------
# By Default swagger ui is available only to admin user(s). You can change permission classes to change that
# See more configuration options at https://drf-spectacular.readthedocs.io/en/latest/settings.html#settings
SPECTACULAR_SETTINGS = {
    "TITLE": "{{cookiecutter.project_name|title}} API",
    "DESCRIPTION": "Documentation of API endpoints of {{cookiecutter.project_name|title}}",
    "VERSION": "1.0.0",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "SCHEMA_PATH_PREFIX": "/api/v[0-9]",
    # Dictionary of general configuration to pass to the SwaggerUI({ ... })
    # https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
    },
    "COMPONENT_SPLIT_REQUEST": True,
    "POSTPROCESSING_HOOKS": [
        "core.restframework.openapi_hooks.wrap_enveloped_responses",
        "core.restframework.openapi_hooks.inject_business_errors",
    ],
}

SHOW_API_DOCS = env.bool("SHOW_API_DOCS", default=DEBUG)

# DJOSER SETTINGS
# ------------------------------------------------------------------------------
DJOSER = {
    "SEND_ACTIVATION_EMAIL": False,
    "SERIALIZERS": {
        "user_create": "core.auth.serializers.UserCreateSerializer",
        "user": "core.auth.serializers.UserSerializer",
        "current_user": "core.auth.serializers.UserSerializer",
    },
}

# SIMPLE JWT SETTINGS
# ------------------------------------------------------------------------------

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
}

# LOGGING
# ------------------------------------------------------------------------------
LOG_DIR = BASE_DIR / "logs"
{%- if cookiecutter.use_redis == "yes" %}

CACHES = {
    "default": {
        "BACKEND": "libs.cache.backend.EnhancedRedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "libs.cache.client.EnhancedRedisClient",
        },
    },
    {%- if cookiecutter.use_celery == "yes" %}
    "celery_results": {
        "BACKEND": "libs.cache.backend.EnhancedRedisCache",
        "LOCATION": env("CELERY_RESULTS_REDIS_URL", default="redis://localhost:6379/2"),
        "OPTIONS": {
            "CLIENT_CLASS": "libs.cache.client.EnhancedRedisClient",
        },
    },
    {%- endif %}
}

# THROTTLING
# ------------------------------------------------------------------------------
CONCURRENT_REQUESTS_PER_USER = env.int("CONCURRENT_REQUESTS_PER_USER", default=10)
CONCURRENT_REQUESTS_TIMEOUT = env.int("CONCURRENT_REQUESTS_TIMEOUT", default=60)
THROTTLE_BLACKLIST_TTL = env.int("THROTTLE_BLACKLIST_TTL", default=30)
THROTTLE_IP_ENABLED = env.bool("THROTTLE_IP_ENABLED", default=True)
{%- endif %}
{%- if cookiecutter.use_auditlog == "yes" %}

# AUDITLOG
# Note: bulk_create/bulk_update/QuerySet.update do not trigger audit logging.
# Use obj.save() for auditable changes.
# ------------------------------------------------------------------------------
AUDITLOG_CID_GETTER = "libs.logging.handlers.get_correlation_id"
AUDITLOG_INCLUDE_ALL_MODELS = False
AUDITLOG_RETENTION_DAYS = env.int("AUDITLOG_RETENTION_DAYS", default=90)
{%- endif %}
{%- if cookiecutter.use_celery == "yes" %}

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/1")
{%- if cookiecutter.use_redis == "yes" %}
CELERY_RESULT_BACKEND = "django-cache"
CELERY_CACHE_BACKEND = "celery_results"
{%- else %}
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="django-db")
CELERY_RESULT_EXTENDED = True
{%- endif %}
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_WORKER_POOL = "{{ cookiecutter.celery_pool }}"
CELERY_WORKER_CONCURRENCY = env.int("CELERY_WORKER_CONCURRENCY", default=10)
{%- endif %}

# DJ CONTROL ROOM
# MCP note: dj-control-room resolves MCP_USERNAME via the `username` field,
# which is absent when username_type=email (upstream fix pending).
# ------------------------------------------------------------------------------
DJ_CONTROL_ROOM_MCP_TOKEN = env("DJ_CONTROL_ROOM_MCP_TOKEN", default="")
DJ_CONTROL_ROOM_SETTINGS = {
    "MCP_ENABLED": env.bool("DJ_CONTROL_ROOM_MCP_ENABLED", default=True),
    "MCP_TOKEN": DJ_CONTROL_ROOM_MCP_TOKEN,
    "MCP_USERNAME": env("DJ_CONTROL_ROOM_MCP_USERNAME", default="admin"),
    "EXTRA_CSS": [] if DEBUG else ["core_admin/css/dcr_dashboard.css"],
}

DJ_URLS_PANEL_SETTINGS = {
    "EXCLUDE_URLS": [
        r".*\?P<format>",
        r".*<drf_format_suffix:format>",
    ],
}
{%- if cookiecutter.use_redis == "yes" %}

DJ_REDIS_PANEL_SETTINGS = {
    "INSTANCES": {
        "cache": {"url": env("REDIS_URL", default="redis://localhost:6379/0")},
        {%- if cookiecutter.use_celery == "yes" %}
        "celery-broker": {"url": env("CELERY_BROKER_URL", default="redis://localhost:6379/1")},
        "celery-results": {"url": env("CELERY_RESULTS_REDIS_URL", default="redis://localhost:6379/2")},
        {%- endif %}
    },
}
{%- endif %}


UNFOLD = {
    "SITE_TITLE": "{{ cookiecutter.project_name }}",
    "SITE_HEADER": "{{ cookiecutter.project_name }}",
    "SITE_SUBHEADER": "{{ cookiecutter.description }}",
    "SITE_SYMBOL": "speed",
    "SHOW_HISTORY": True,
    "SHOW_SIDEBAR": True,
    "ENVIRONMENT": "core.admin.callbacks.environment_callback",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": "core.admin.navigation.sidebar_navigation",
    },
}

# ADMIN GATE
# ------------------------------------------------------------------------------
# Seed value for the Constance ADMIN_SECURITY_CODE config below.
# Once changed in the admin, the stored Constance value takes precedence.
ADMIN_SECURITY_CODE = env("ADMIN_SECURITY_CODE", default="")

# DJANGO GUID
# ------------------------------------------------------------------------------
DJANGO_GUID = {
    "GUID_HEADER_NAME": "Correlation-ID",
    "VALIDATE_GUID": True,
    "RETURN_HEADER": True,
    "EXPOSE_HEADER": True,
    "INTEGRATIONS": [
        {%- if cookiecutter.use_celery == "yes" %}
        CeleryIntegration(use_django_logging=True, log_parent=True),
        {%- endif %}
    ],
    "IGNORE_URLS": ["/health/", "/ready/", "/alive/"],
    "UUID_LENGTH": 32,
}

# CONSTANCE
# ------------------------------------------------------------------------------
{%- if cookiecutter.use_redis == "yes" %}
CONSTANCE_BACKEND = "constance.backends.redisd.RedisBackend"
CONSTANCE_REDIS_CONNECTION = env("REDIS_URL", default="redis://localhost:6379/0")
CONSTANCE_REDIS_PREFIX = "constance:"
{%- else %}
CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_DATABASE_CACHE_BACKEND = None
{%- endif %}
CONSTANCE_SUPERUSER_ONLY = True
CONSTANCE_ADDITIONAL_FIELDS = {**UNFOLD_CONSTANCE_ADDITIONAL_FIELDS}

CONSTANCE_CONFIG = {
    "SITE_NAME": (
        "{{ cookiecutter.project_name }}",
        "Site display name",
        str,
    ),
    "MAINTENANCE_MODE": (
        False,
        "Enable maintenance mode (returns 503)",
        bool,
    ),
    "ADMIN_SECURITY_CODE": (
        ADMIN_SECURITY_CODE,
        "If set, /admin/ is hidden until unlocked via /admin/<code>/. Empty disables the gate.",
        str,
    ),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "General": {"fields": ("SITE_NAME",)},
    "System": {"fields": ("MAINTENANCE_MODE", "ADMIN_SECURITY_CODE")},
}
