from typing import Any

from rest_framework.renderers import JSONRenderer


class UnifiedJSONRenderer(JSONRenderer):
    def render(
        self,
        data: Any,
        accepted_media_type: str | None = None,
        renderer_context: dict[str, Any] | None = None,
    ) -> bytes:
        response = None
        if renderer_context is not None:
            response = renderer_context.get("response")

        if response is not None and getattr(response, "exception", False):
            return super().render(
                data,
                accepted_media_type=accepted_media_type,
                renderer_context=renderer_context,
            )

        if response is not None and getattr(response, "status_code", 200) >= 400:
            if isinstance(data, dict) and {"code", "data", "message"}.issubset(data.keys()):
                return super().render(
                    data,
                    accepted_media_type=accepted_media_type,
                    renderer_context=renderer_context,
                )

            message = "error"
            if isinstance(data, dict) and "detail" in data:
                message = str(data.get("detail"))

            wrapped_error = {
                "code": "REQ_1000" if 400 <= response.status_code < 500 else "SYS_5000",
                "data": {"errors": data} if data is not None else {},
                "message": message,
            }
            return super().render(
                wrapped_error,
                accepted_media_type=accepted_media_type,
                renderer_context=renderer_context,
            )

        if isinstance(data, dict) and {"code", "data", "message"}.issubset(data.keys()):
            return super().render(
                data,
                accepted_media_type=accepted_media_type,
                renderer_context=renderer_context,
            )

        wrapped = {
            "code": 0,
            "data": data if data is not None else {},
            "message": "success",
        }
        return super().render(
            wrapped,
            accepted_media_type=accepted_media_type,
            renderer_context=renderer_context,
        )
