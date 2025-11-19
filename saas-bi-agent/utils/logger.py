"""
Structured logging setup for SaaS BI Agent system.
Provides JSON and text logging with trace/session context.
"""

import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler
import contextvars

# Context variables for request tracing
trace_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('trace_id', default=None)
session_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('session_id', default=None)


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    Includes trace_id and session_id from context.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record

        Returns:
            JSON formatted log string
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add trace context if available
        trace_id = trace_id_var.get()
        if trace_id:
            log_data['trace_id'] = trace_id

        session_id = session_id_var.get()
        if session_id:
            log_data['session_id'] = session_id

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """
    Custom text formatter with color support and trace context.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def __init__(self, use_colors: bool = True):
        """
        Initialize text formatter.

        Args:
            use_colors: Whether to use ANSI colors
        """
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as colored text.

        Args:
            record: Log record

        Returns:
            Formatted log string
        """
        # Base format
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname

        # Add color if enabled
        if self.use_colors:
            color = self.COLORS.get(level, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            level = f"{color}{level}{reset}"

        # Build log message
        parts = [
            f"[{timestamp}]",
            f"[{level}]",
            f"[{record.name}]"
        ]

        # Add trace context if available
        trace_id = trace_id_var.get()
        if trace_id:
            parts.append(f"[trace:{trace_id[:8]}]")

        session_id = session_id_var.get()
        if session_id:
            parts.append(f"[session:{session_id[:8]}]")

        parts.append(record.getMessage())

        log_line = " ".join(parts)

        # Add exception if present
        if record.exc_info:
            log_line += "\n" + self.formatException(record.exc_info)

        return log_line


class StructuredLogger(logging.LoggerAdapter):
    """
    Logger adapter that supports structured logging with extra fields.
    """

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Process log message and kwargs to add extra fields.

        Args:
            msg: Log message
            kwargs: Additional kwargs

        Returns:
            Processed (msg, kwargs) tuple
        """
        # Extract extra data
        extra_data = kwargs.pop('extra_data', {})

        # Add to extra dict for the formatter
        if 'extra' not in kwargs:
            kwargs['extra'] = {}

        kwargs['extra']['extra_data'] = extra_data

        return msg, kwargs

    def log_with_context(self, level: int, msg: str, **kwargs):
        """
        Log with additional context fields.

        Args:
            level: Log level
            msg: Log message
            **kwargs: Additional context fields
        """
        self.log(level, msg, extra_data=kwargs)

    def debug_ctx(self, msg: str, **kwargs):
        """Debug log with context."""
        self.log_with_context(logging.DEBUG, msg, **kwargs)

    def info_ctx(self, msg: str, **kwargs):
        """Info log with context."""
        self.log_with_context(logging.INFO, msg, **kwargs)

    def warning_ctx(self, msg: str, **kwargs):
        """Warning log with context."""
        self.log_with_context(logging.WARNING, msg, **kwargs)

    def error_ctx(self, msg: str, **kwargs):
        """Error log with context."""
        self.log_with_context(logging.ERROR, msg, **kwargs)

    def critical_ctx(self, msg: str, **kwargs):
        """Critical log with context."""
        self.log_with_context(logging.CRITICAL, msg, **kwargs)


def setup_logging(
    level: str = "INFO",
    log_format: str = "json",
    output: str = "stdout",
    file_path: Optional[str] = None,
    max_file_size_mb: int = 100,
    backup_count: int = 5
) -> None:
    """
    Setup application-wide logging configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ('json' or 'text')
        output: Output destination ('stdout', 'file', or 'both')
        file_path: Path to log file (if output includes 'file')
        max_file_size_mb: Maximum log file size in MB before rotation
        backup_count: Number of backup files to keep
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Add stdout handler
    if output in ("stdout", "both"):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler
    if output in ("file", "both") and file_path:
        # Ensure log directory exists
        log_file = Path(file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set levels for noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        StructuredLogger instance
    """
    logger = logging.getLogger(name)
    return StructuredLogger(logger, {})


def set_trace_context(trace_id: Optional[str] = None, session_id: Optional[str] = None):
    """
    Set trace context for current execution.

    Args:
        trace_id: Trace ID to set
        session_id: Session ID to set
    """
    if trace_id:
        trace_id_var.set(trace_id)
    if session_id:
        session_id_var.set(session_id)


def clear_trace_context():
    """Clear trace context."""
    trace_id_var.set(None)
    session_id_var.set(None)


def get_trace_id() -> Optional[str]:
    """Get current trace ID from context."""
    return trace_id_var.get()


def get_session_id() -> Optional[str]:
    """Get current session ID from context."""
    return session_id_var.get()


# Example usage
if __name__ == "__main__":
    # Setup logging
    setup_logging(level="DEBUG", log_format="text", output="stdout")

    # Get logger
    logger = get_logger(__name__)

    # Set trace context
    set_trace_context(trace_id="trace-123", session_id="session-456")

    # Basic logging
    logger.info("Application started")
    logger.debug("Debug information")
    logger.warning("Warning message")

    # Structured logging with context
    logger.info_ctx(
        "User action performed",
        user_id="user-789",
        action="create_analysis",
        duration_ms=150
    )

    # Error logging
    try:
        raise ValueError("Sample error")
    except Exception as e:
        logger.error("Error occurred", exc_info=True)

    # Clear context
    clear_trace_context()
