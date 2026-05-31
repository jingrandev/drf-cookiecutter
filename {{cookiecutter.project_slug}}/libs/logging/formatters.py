import traceback as stdlib_traceback

import stackprinter


class ErrorFormatter:
    """Format exceptions using stackprinter for readable error stacks.

    Falls back to stdlib traceback formatting when stackprinter cannot handle
    the exception (e.g. billiard.einfo.Traceback from Celery workers).
    """

    def __init__(self) -> None:
        self.default_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {elapsed} | {level: <8} | "
            "[{extra[correlation_id]}] [{process.id}] "
            "{name}:{function}:{line} - {message}\n"
        )

    def format_exception(self, record):
        if record.get("exception") is not None:
            exc = record["exception"]
            try:
                stack = stackprinter.format(exc, show_vals="like_source", source_lines=10)
            except (ValueError, TypeError):
                stack = "".join(stdlib_traceback.format_exception(*exc))
            record["extra"]["stack"] = stack
            return self.default_format + "{extra[stack]}\n"
        return self.default_format

    def __call__(self, record):
        return self.format_exception(record)
