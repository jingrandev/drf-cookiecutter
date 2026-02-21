from typing import Any

from django.utils.encoding import force_str


def _is_enveloped_schema(schema: Any) -> bool:
    if not isinstance(schema, dict):
        return False
    if schema.get("type") != "object":
        return False
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return False
    return {"code", "data", "message"}.issubset(properties.keys())


def _envelope_schema(inner_schema: Any) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "code": {
                "oneOf": [
                    {"type": "integer", "example": 0},
                    {"type": "string", "example": "AUTH_1001"},
                ]
            },
            "data": inner_schema if inner_schema is not None else {"type": "object"},
            "message": {"type": "string", "example": "success"},
        },
        "required": ["code", "data", "message"],
    }


def wrap_enveloped_responses(
    result: dict[str, Any], generator: Any, request: Any, public: bool
) -> dict[str, Any]:
    paths = result.get("paths")
    if not isinstance(paths, dict):
        return result

    for _path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for _method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue

            responses = operation.get("responses")
            if not isinstance(responses, dict):
                continue

            for _status, response in responses.items():
                if not isinstance(response, dict):
                    continue

                content = response.get("content")
                if not isinstance(content, dict):
                    continue

                json_ct = content.get("application/json")
                if not isinstance(json_ct, dict):
                    continue

                schema = json_ct.get("schema")
                if schema is None or _is_enveloped_schema(schema):
                    continue

                json_ct["schema"] = _envelope_schema(schema)

    return result


def inject_business_errors(
    result: dict[str, Any], generator: Any, request: Any, public: bool
) -> dict[str, Any]:
    try:
        from core.restframework.error_handler import error_registry
    except Exception:
        return result

    components = result.setdefault("components", {})
    schemas = components.setdefault("schemas", {})

    items: list[dict[str, Any]] = []
    codes: list[str] = []

    for code, exc_cls in error_registry.items():
        code_str = str(code)
        codes.append(code_str)
        message = getattr(exc_cls, "message", "")
        items.append(
            {
                "code": code_str,
                "message": force_str(message) if message is not None else "",
                "exception": f"{exc_cls.__module__}.{exc_cls.__name__}",
            }
        )

    codes = sorted(set(codes))
    items = sorted(items, key=lambda x: x.get("code", ""))

    schemas.setdefault(
        "BusinessErrorCode",
        {
            "type": "string",
            "description": "Registered business error codes (BaseError subclasses).",
            "enum": codes,
        },
    )

    schemas.setdefault(
        "BusinessErrorCatalog",
        {
            "type": "object",
            "description": "Catalog of registered business errors (code/message).",
            "properties": {
                "errors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "code": {"$ref": "#/components/schemas/BusinessErrorCode"},
                            "message": {"type": "string"},
                            "exception": {"type": "string"},
                        },
                        "required": ["code", "message"],
                    },
                    "example": items,
                }
            },
        },
    )

    return result
