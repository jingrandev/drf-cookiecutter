# ruff: noqa: PGH004, F405, F403
from .base import *

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": [
        "debug_toolbar.panels.redirects.RedirectsPanel",
        "debug_toolbar.panels.profiling.ProfilingPanel",
    ],
    "SHOW_TEMPLATE_CONTEXT": True,
}
INTERNAL_IPS = ["127.0.0.1"]

INSTALLED_APPS += ["silk"]
MIDDLEWARE = ["silk.middleware.SilkyMiddleware", *MIDDLEWARE]
SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_MAX_RECORDED_REQUESTS = 500
SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT = 10
SILKY_INTERCEPT_PERCENT = 100
SILKY_MAX_REQUEST_BODY_SIZE = -1
SILKY_MAX_RESPONSE_BODY_SIZE = -1
SILKY_AUTHENTICATION = False
SILKY_AUTHORISATION = False
SILKY_META = True
SILKY_PYTHON_PROFILER_RESULT_PATH = BASE_DIR / "silk"
SILKY_PYTHON_PROFILER_RESULT_PATH.mkdir(parents=True, exist_ok=True)

SHOW_API_DOCS = True
