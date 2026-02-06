"""Structured logging configuration for pygramattic-reports.

Configures ``structlog`` with timestamped, level-filtered output
supporting both human-readable console and JSON formats.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from pygramattic_reports.config.settings import LoggingConfig


def _name_to_level(name: str) -> int:
    """Convert a log level name to its numeric value.

    Args:
        name: Log level name (e.g. ``"DEBUG"``, ``"INFO"``).

    Returns:
        The numeric log level, defaulting to 20 (INFO) for
        unrecognised names.
    """
    levels = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50,
    }
    return levels.get(name.upper(), 20)


def setup_logging(config: LoggingConfig) -> None:
    """Configure structured logging for the application.

    Call this once at application startup (in CLI main).

    Args:
        config: Logging configuration from ``AppConfig``.
    """
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if config.format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            _name_to_level(config.level),
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(module: str) -> Any:  # noqa: ANN401
    """Get a structured logger for a specific module.

    Args:
        module: Module name for log correlation
            (e.g. ``"loaders"``, ``"builder"``).

    Returns:
        A bound structlog logger with the module name attached.

    Example::

        logger = get_logger("loaders")
        logger.info("Loading file", path="/data/input.csv", format="csv")
    """
    return structlog.get_logger(module=module)
