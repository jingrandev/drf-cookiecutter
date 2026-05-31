import logging
import sys
from pathlib import Path

from django.conf import settings
from loguru import logger

from libs.logging.formatters import ErrorFormatter
from libs.logging.handlers import LoguruHandler

STDOUT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "[{extra[correlation_id]}] [{process.id}] "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "[{extra[correlation_id]}] [{process.id}] "
    "{name}:{function}:{line} - {message}"
)


def setup_logging():
    logger.remove()
    log_dir = settings.LOG_DIR
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    debug = getattr(settings, "DEBUG", False)
    log_level = getattr(settings, "LOG_LEVEL", "INFO")
    file_log_level = getattr(settings, "FILE_LOG_LEVEL", "INFO")
    enable_enqueue = getattr(settings, "LOG_ENQUEUE", True)
    enable_backtrace = getattr(settings, "LOG_BACKTRACE", debug)
    enable_diagnose = getattr(settings, "LOG_DIAGNOSE", debug)

    config = {
        "handlers": [
            {
                "sink": sys.stdout,
                "level": log_level,
                "enqueue": enable_enqueue,
                "backtrace": enable_backtrace,
                "diagnose": enable_diagnose,
                "filter": lambda r: r["level"].no < logger.level("WARNING").no,
                "format": STDOUT_FORMAT,
            },
            {
                "sink": sys.stderr,
                "level": log_level,
                "enqueue": enable_enqueue,
                "backtrace": enable_backtrace,
                "diagnose": enable_diagnose,
                "filter": lambda r: r["level"].no >= logger.level("WARNING").no,
                "format": ErrorFormatter(),
            },
            {
                "sink": Path(log_dir) / "info.log",
                "level": file_log_level,
                "rotation": "00:00",
                "retention": "1 week",
                "enqueue": enable_enqueue,
                "backtrace": enable_backtrace,
                "diagnose": enable_diagnose,
                "format": FILE_FORMAT,
            },
            {
                "sink": Path(log_dir) / "error.log",
                "level": "ERROR",
                "rotation": "00:00",
                "retention": "1 week",
                "enqueue": enable_enqueue,
                "backtrace": True,
                "diagnose": enable_diagnose,
                "format": ErrorFormatter(),
            },
            {%- if cookiecutter.use_celery == "yes" %}
            {
                "sink": Path(log_dir) / "celery.log",
                "level": file_log_level,
                "rotation": "00:00",
                "retention": "1 week",
                "enqueue": enable_enqueue,
                "backtrace": enable_backtrace,
                "diagnose": enable_diagnose,
                "format": FILE_FORMAT,
                "filter": lambda r: r["name"].startswith(("celery", "kombu")),
            },
            {
                "sink": Path(log_dir) / "celery-error.log",
                "level": "ERROR",
                "rotation": "00:00",
                "retention": "1 week",
                "enqueue": enable_enqueue,
                "backtrace": True,
                "diagnose": enable_diagnose,
                "format": ErrorFormatter(),
                "filter": lambda r: r["name"].startswith(("celery", "kombu")),
            },
            {%- endif %}
        ],
    }

    logging.basicConfig(handlers=[LoguruHandler()], level=0, force=True)
    logger.configure(**config)
