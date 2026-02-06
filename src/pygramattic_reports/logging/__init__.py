"""Logging and build tracking for pygramattic-reports.

Structured logging via structlog with per-module loggers,
build log tracking, and performance timing.

Usage::

    from pygramattic_reports.logging import setup_logging, get_logger

    setup_logging(config.logging)
    logger = get_logger("loaders")
    logger.info("Loading file", path="data.csv")
"""

from .build_log import BuildLog, BuildLogEntry
from .setup import get_logger, setup_logging

__all__ = ["BuildLog", "BuildLogEntry", "get_logger", "setup_logging"]
