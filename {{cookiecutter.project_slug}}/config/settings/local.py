# ruff: noqa: PGH004, F405, F403
import os

from .base import *

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-development-key-for-local-use-only"

# Django Debug Toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
INSTALLED_APPS += ["debug_toolbar"]
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": [
        "debug_toolbar.panels.redirects.RedirectsPanel",
        # Disable profiling panel due to an issue with Python 3.12:
        # https://github.com/jazzband/django-debug-toolbar/issues/1875
        "debug_toolbar.panels.profiling.ProfilingPanel",
    ],
    "SHOW_TEMPLATE_CONTEXT": True,
}

# Internal IPs for debug toolbar
INTERNAL_IPS = ["127.0.0.1"]

# SILK SETTINGS
# ------------------------------------------------------------------------------
INSTALLED_APPS += ["silk"]
MIDDLEWARE = ["silk.middleware.SilkyMiddleware", *MIDDLEWARE]

SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_MAX_RECORDED_REQUESTS = 10_000
SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT = 10
SILKY_INTERCEPT_PERCENT = 100  # Record all requests by default
SILKY_MAX_REQUEST_BODY_SIZE = -1  # No limit
SILKY_MAX_RESPONSE_BODY_SIZE = -1  # No limit
SILKY_AUTHENTICATION = False
SILKY_AUTHORISATION = False
SILKY_META = True  # Include metadata like request headers
SILKY_PYTHON_PROFILER_RESULT_PATH = BASE_DIR / "silk"
SILKY_PYTHON_PROFILER_RESULT_PATH.mkdir(parents=True, exist_ok=True)

# API Documentation
SHOW_API_DOCS = True

# LOGGING
# ------------------------------------------------------------------------------
# Print Django ORM raw SQL queries to loguru via the stdlib bridge.
# Only active in local development — SQL query volume is too high for production.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "loggers": {
        "django.db.backends": {
            "level": "DEBUG",
        },
    },
}
