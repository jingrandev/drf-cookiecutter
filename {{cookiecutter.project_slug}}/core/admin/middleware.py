import hmac

from constance import config
from django.http import Http404
from django.shortcuts import redirect

SESSION_KEY = "admin_gate_unlocked"


class AdminGateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        code = config.ADMIN_SECURITY_CODE
        if not code or not request.path.startswith("/admin/"):
            return self.get_response(request)
        if request.path.rstrip("/") == f"/admin/{code}":
            request.session[SESSION_KEY] = True
            return redirect("admin:index")
        if request.session.get(SESSION_KEY):
            return self.get_response(request)
        raise Http404
