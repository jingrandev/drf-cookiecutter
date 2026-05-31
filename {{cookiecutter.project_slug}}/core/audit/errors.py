from rest_framework import status

from core.restframework.error_handler import BaseError


class ActionNotFoundError(BaseError):
    code = "AUDIT_1001"
    message = "action not found"
    http_status = status.HTTP_404_NOT_FOUND


class ActionNotUndoableError(BaseError):
    code = "AUDIT_1002"
    message = "action does not support undo"
    http_status = status.HTTP_400_BAD_REQUEST


class ActionNotRedoableError(BaseError):
    code = "AUDIT_1003"
    message = "action does not support redo"
    http_status = status.HTTP_400_BAD_REQUEST
