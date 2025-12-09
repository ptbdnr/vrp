"""Logging module."""

import json
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, ClassVar, Literal


class Logger:
    """Production-ready logger with support for multiple output channels and log levels.

    Features:
    - Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Console (stdout/stderr) output
    - File output with rotation
    - JSON formatting option
    - Context management support
    - Thread-safe operations
    """

    # Log level mapping
    LEVELS: ClassVar = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    def __init__(
        self,
        name: str,
        level: str = "INFO",
        *,
        console_output: bool = True,
        file_output: str | None = None,
        json_format: bool = False,
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5,
        date_format: str = "%Y-%m-%d %H:%M:%S",
    ) -> None:
        """Initialize the logger.

        Args:
            name: Logger name (typically __name__ of the module)
            level: Minimum log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            console_output: Enable console output to stdout
            file_output: Path to log file (None to disable file logging)
            json_format: Use JSON format for log messages
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            date_format: Date format for log messages

        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.LEVELS.get(level.upper(), logging.INFO))
        self.logger.propagate = False
        self.json_format = json_format
        self.date_format = date_format

        # Remove existing handlers
        self.logger.handlers.clear()

        # Add console handler
        if console_output:
            self._add_console_handler()

        # Add file handler
        if file_output:
            self._add_file_handler(file_output, max_bytes, backup_count)

    def _add_console_handler(self) -> None:
        """Add console handler for stdout output."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.logger.level)
        console_handler.setFormatter(self._get_formatter())
        self.logger.addHandler(console_handler)

    def _add_file_handler(self, filepath: str, max_bytes: int, backup_count: int) -> None:
        """Add rotating file handler."""
        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filepath,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(self.logger.level)
        file_handler.setFormatter(self._get_formatter())
        self.logger.addHandler(file_handler)

    def _get_formatter(self) -> logging.Formatter:
        """Get appropriate formatter based on configuration."""
        if self.json_format:
            return JsonFormatter(self.date_format)
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
        return logging.Formatter(format_string, datefmt=self.date_format)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, exc_info=exc_info, extra=kwargs)

    def critical(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(message, exc_info=exc_info, extra=kwargs)

    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback."""
        self.logger.exception(message, extra=kwargs)

    def set_level(
            self,
            level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        ) -> None:
        """Change the logging level dynamically."""
        if level.upper() not in self.LEVELS:
            available = ", ".join(self.LEVELS.keys())
            msg = f"Invalid log level '{level}'. Must be one of: {available}"
            raise ValueError(msg)

        new_level = self.LEVELS[level.upper()]
        self.logger.setLevel(new_level)
        for handler in self.logger.handlers:
            handler.setLevel(new_level)

        self.info(f"Log level changed to {level.upper()}")

    def get_level(self) -> str:
        """Get the current logging level.

        Returns:
            Current log level as string (e.g., 'INFO', 'DEBUG')

        """
        level_num = self.logger.level
        for name, num in self.LEVELS.items():
            if num == level_num:
                return name
        return "NOTSET"

    @property
    def level(self) -> str:
        """Get current log level as a property."""
        return self.get_level()

    @level.setter
    def level(self, value: str):
        """Set log level using property assignment."""
        self.set_level(value)

    def add_context(self, **context) -> "LoggerContext":
        """Add context information to subsequent log messages.

        Usage:
            with logger.add_context(user_id=123, request_id='abc'):
                logger.info('Processing request')
        """
        return LoggerContext(self, context)


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def __init__(self, date_format: str):
        super().__init__()
        self.date_format = date_format

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).strftime(self.date_format),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class LoggerContext:
    """Context manager for adding contextual information to logs."""

    def __init__(self, logger: Logger, context: dict[str, Any]) -> None:
        """Initialize the context manager."""
        self.logger = logger
        self.context = context
        self.old_factory = None

    def __enter__(self) -> "LoggerContext":
        """Enter context and add context data to log records."""
        self.old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs) -> logging.LogRecord:
            record = self.old_factory(*args, **kwargs)
            if not hasattr(record, "extra_fields"):
                record.extra_fields = {}
            record.extra_fields.update(self.context)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and restore original factory."""
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)


# Example usage
if __name__ == "__main__":
    # Basic console logging
    logger = Logger("myapp", level="DEBUG")
    logger.info("Application started")
    logger.debug("Debug information")
    logger.warning("Warning message")
    logger.error("Error occurred")

    # File logging with rotation
    file_logger = Logger(
        "myapp.file",
        level="INFO",
        console_output=True,
        file_output="logs/application.log",
        max_bytes=1048576,  # 1MB
        backup_count=3,
    )
    file_logger.info("Logging to file and console")

    # JSON formatted logging
    json_logger = Logger(
        "myapp.json",
        level="INFO",
        json_format=True,
    )
    json_logger.info("Structured logging message")

    # Context logging
    with logger.add_context(user_id=12345, session="abc-def"):
        logger.info("User action performed")
        logger.warning("Suspicious activity detected")

    # Exception logging
    try:
        result = 1 / 0
    except Exception:
        logger.exception("Division by zero occurred")
