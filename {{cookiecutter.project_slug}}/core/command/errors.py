from rest_framework import status

from core.restframework.error_handler import BaseError


class CommandNotFoundError(BaseError):
    code = "CMD_1001"
    message = "command not found"
    http_status = status.HTTP_404_NOT_FOUND


class CommandNotUndoableError(BaseError):
    code = "CMD_1002"
    message = "command does not support undo"
    http_status = status.HTTP_400_BAD_REQUEST


class CommandNotRedoableError(BaseError):
    code = "CMD_1003"
    message = "command does not support redo"
    http_status = status.HTTP_400_BAD_REQUEST
