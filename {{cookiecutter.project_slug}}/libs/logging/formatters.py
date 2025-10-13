import stackprinter


class ErrorFormatter:
    """Format exceptions using stackprinter for readable error stacks."""

    def __init__(self) -> None:
        # Default log line with process/thread identifiers for diagnostics
        self.default_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {elapsed} | {level: <8} | "
            "pid={process.id} tid={thread.id} | "
            "{name}:{function}:{line} - {message}\n"
        )

    def format_exception(self, record):
        """Format error record and append pretty-printed stack when available."""
        if record.get("exception") is not None:
            exc = record["exception"]
            stack = stackprinter.format(exc, show_vals="like_source", source_lines=10)
            record["extra"]["stack"] = stack
            return self.default_format + "{extra[stack]}\n"
        return self.default_format

    def __call__(self, record):
        """Callable interface required by Loguru for dynamic formatting."""
        return self.format_exception(record)
