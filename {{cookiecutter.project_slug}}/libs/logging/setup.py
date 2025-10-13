import logging
import sys
from pathlib import Path

from django.conf import settings
from loguru import logger

from libs.logging.handlers import LoguruHandler
from libs.logging.filters import single_level_filter
from libs.logging.formatters import ErrorFormatter


def setup_logging():
    """
    Configure logging for Django using Loguru.
    """
    logger.remove()
    log_dir = settings.LOG_DIR
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    debug = getattr(settings, "DEBUG", False)
    log_level = getattr(settings, "LOG_LEVEL", "INFO")
    file_log_level = getattr(settings, "FILE_LOG_LEVEL", "INFO")
    enable_enqueue = getattr(settings, "LOG_ENQUEUE", True)
    enable_backtrace = getattr(settings, "LOG_BACKTRACE", debug)
    enable_diagnose = getattr(settings, "LOG_DIAGNOSE", debug)

    # Configure loguru
    config = {
        "handlers": [
            {
                "sink": sys.stdout,
                "level": log_level,
                "enqueue": enable_enqueue,
                "backtrace": enable_backtrace,
                "diagnose": enable_diagnose,
                "filter": lambda r: r["level"].no < logger.level("WARNING").no,
                "format": (
                    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                    "<level>{level: <8}</level> | "
                    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                    "<level>{message}</level>"
                ),
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
                "sink": Path(log_dir) / "app.log",
                "level": file_log_level,
                "rotation": "10 MB",
                "retention": "1 week",
                "enqueue": enable_enqueue,
                "backtrace": enable_backtrace,
                "diagnose": enable_diagnose,
                "format": (
                    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                    "{level: <8} | {name}:{function}:{line} - {message}"
                ),
            },
            {
                "sink": Path(log_dir) / "error.log",
                "level": "DEBUG",
                "rotation": "10 MB",
                "retention": "1 week",
                "enqueue": enable_enqueue,
                "backtrace": enable_backtrace,
                "diagnose": enable_diagnose,
                "format": ErrorFormatter(),
                "filter": lambda record: single_level_filter(record, "ERROR"),
            },
        ],
    }

    logging.basicConfig(handlers=[LoguruHandler()], level=0, force=True)
    logger.configure(**config)
