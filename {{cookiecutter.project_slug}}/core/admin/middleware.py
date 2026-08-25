import hmac

from constance import config
from django.http import Http404
from django.shortcuts import redirect

SESSION_KEY = "admin_gate_unlocked"

# dj-control-room's MCP endpoint authenticates via Bearer token on every
# request (no session), so it must bypass the gate.
MCP_PATH = "/admin/dj-control-room/mcp"


class AdminGateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        code = config.ADMIN_SECURITY_CODE
        if not code or not request.path.startswith("/admin/"):
            return self.get_response(request)
        if request.path.rstrip("/") == MCP_PATH:
            return self.get_response(request)
        if request.path.rstrip("/") == f"/admin/{code}":
            request.session[SESSION_KEY] = True
            return redirect("admin:index")
        if request.session.get(SESSION_KEY):
            return self.get_response(request)
        raise Http404
