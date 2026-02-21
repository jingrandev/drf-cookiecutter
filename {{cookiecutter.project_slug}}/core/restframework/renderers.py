from typing import Any

from rest_framework.renderers import JSONRenderer


class StandardResponseRenderer(JSONRenderer):
    def is_envelope(self, data: Any) -> bool:
        if not isinstance(data, dict):
            return False
        if not {"code", "data", "message"}.issubset(data.keys()):
            return False
        if not isinstance(data.get("message"), str):
            return False
        return True

    def wrap_success(self, data: Any) -> dict[str, Any]:
        return {
            "code": 0,
            "data": data if data is not None else {},
            "message": "success",
        }

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

        if self.is_envelope(data):
            return super().render(
                data,
                accepted_media_type=accepted_media_type,
                renderer_context=renderer_context,
            )

        return super().render(
            self.wrap_success(data),
            accepted_media_type=accepted_media_type,
            renderer_context=renderer_context,
        )
