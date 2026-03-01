import logging
import sys

# ANSI codes
_RESET = "\033[0m"
_DIM   = "\033[2m"
_BOLD  = "\033[1m"

_LEVEL_COLOR = {
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[32m",   # green
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[35m",   # magenta
}


class _ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color = _LEVEL_COLOR.get(record.levelname, _RESET)
        timestamp = self.formatTime(record, "%H:%M:%S")
        level     = f"{color}{record.levelname:<8}{_RESET}"
        # Strip "app." prefix so "app.services.gemini" → "services.gemini"
        name      = record.name.removeprefix("app.")
        name_str  = f"{_DIM}{name:<22}{_RESET}"
        msg       = record.getMessage()

        line = f"{_DIM}{timestamp}{_RESET}  {level}  {name_str}  {msg}"

        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)

        return line


def setup_logging(level: int = logging.DEBUG) -> None:
    """
    Configure structured, colored console logging for the app.

    - App loggers (``app.*``) log at *level* (default DEBUG).
    - Third-party loggers are silenced to WARNING.
    - uvicorn.access is suppressed entirely — the HTTP middleware in main.py
      handles request/response logging instead.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_ColorFormatter())

    # Silence everything by default
    logging.getLogger().setLevel(logging.WARNING)

    # App-wide logger
    app_log = logging.getLogger("app")
    app_log.setLevel(level)
    app_log.addHandler(handler)
    app_log.propagate = False

    # Keep uvicorn startup/error messages but drop per-request access lines
    # (our middleware logs those in a friendlier format)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
