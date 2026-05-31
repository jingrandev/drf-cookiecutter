import inspect
import logging
import os
from threading import local

from django_guid import get_guid
from loguru import logger

LOGGING_PATHS: set[str] = {
    os.path.dirname(logging.__file__),
    os.path.dirname(os.path.abspath(__file__)),
}

correlation_override = local()


def set_correlation_id(correlation_id: str):
    correlation_override.correlation_id = correlation_id


def clear_correlation_id():
    try:
        del correlation_override.correlation_id
    except AttributeError:
        pass


def get_correlation_id():
    override = getattr(correlation_override, "correlation_id", None)
    if override:
        return override
    return get_guid() or "-"


def safe_message(message):
    if "<" in message or ">" in message or "{" in message or "}" in message:
        return (
            message.replace("<", r"\<")
            .replace(">", r"\>")
            .replace("{", r"\{")
            .replace("}", r"\}")
        )
    return message


class LoguruHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = inspect.currentframe(), 0
        while frame:
            filename = frame.f_code.co_filename
            if depth > 0 and not any(filename.startswith(p) for p in LOGGING_PATHS):
                break
            frame = frame.f_back
            depth += 1

        correlation_id = get_correlation_id()

        (
            logger.opt(
                exception=record.exc_info,
                depth=depth,
                colors=True,
                lazy=True,
            )
            .bind(correlation_id=correlation_id)
            .log(level, safe_message(record.getMessage()))
        )
