from constance import config
from django.conf import settings
from django.http import JsonResponse
from loguru import logger

MAINTENANCE_EXEMPT_PREFIXES = ("/admin/", "/health/", "/ready/", "/alive/", "/api/v1/health/")


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not config.MAINTENANCE_MODE:
            return self.get_response(request)
        if request.path.startswith(MAINTENANCE_EXEMPT_PREFIXES):
            return self.get_response(request)
        return JsonResponse(
            {
                "code": "SYS_4503",
                "data": {},
                "message": "service under maintenance",
            },
            status=503,
        )


class UnifiedAPIExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception:
            if request.path.startswith("/api/"):
                if getattr(settings, "PROPAGATE_API_EXCEPTIONS", False):
                    raise

                logger.exception(
                    "Unhandled exception caught by UnifiedAPIExceptionMiddleware"
                )
                return JsonResponse(
                    {
                        "code": "SYS_5000",
                        "data": {},
                        "message": "internal error",
                    },
                    status=500,
                )
            raise
