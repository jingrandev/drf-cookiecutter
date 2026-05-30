import inspect
import logging
import os

from loguru import logger

_LOGGING_PATHS: set[str] = {os.path.dirname(logging.__file__), os.path.dirname(os.path.abspath(__file__))}


def safe_message(message):
    return (
        message.replace("<", r"\<")
        .replace(">", r"\>")
        .replace("{", r"\{")
        .replace("}", r"\}")
    )


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
            if depth > 0 and not any(filename.startswith(p) for p in _LOGGING_PATHS):
                break
            frame = frame.f_back
            depth += 1

        logger.opt(
            exception=record.exc_info,
            depth=depth,
            colors=True,
            lazy=True,
        ).log(level, safe_message(record.getMessage()))
