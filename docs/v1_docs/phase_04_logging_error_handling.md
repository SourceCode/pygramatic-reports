# Phase 04: Logging & Error Handling

## Objective

Implement structured logging and a typed exception hierarchy. These cross-cutting concerns are used by every module and must be established before any business logic is written.

## Why This Phase Is Fourth

The PRD lists "clear error messages" as a quality attribute but defines zero error types or behaviors. Every module from Phase 05 onward needs to raise typed exceptions and emit structured log messages. Building these facilities now ensures consistent error handling across the entire codebase.

## Tasks

### Task 4.1: Define Exception Hierarchy

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/exceptions.py`

**Description:** Create a typed exception hierarchy where each module has its own exception class. All exceptions carry context about what went wrong and where.

**Requirements:**
- Base exception: `PygramatticError`
- Each module gets a subclass
- All exceptions carry `message`, `error_code`, `context` (dict of relevant info)
- Exceptions are categorized: fatal, recoverable, retriable

```python
from enum import Enum


class ErrorSeverity(str, Enum):
    """How the pipeline should react to this error."""
    FATAL = "fatal"             # Stop the pipeline immediately
    RECOVERABLE = "recoverable" # Skip the affected section, warn, continue
    RETRIABLE = "retriable"     # Retry with backoff, then degrade


class PygramatticError(Exception):
    """Base exception for all pygramattic-reports errors.

    All exceptions carry structured context for logging and debugging.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN",
        severity: ErrorSeverity = ErrorSeverity.FATAL,
        context: dict | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.context = context or {}
        super().__init__(message)


class ConfigError(PygramatticError):
    """Configuration is invalid, missing, or unparseable."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)


class LoaderError(PygramatticError):
    """Failed to load data from a source."""
    def __init__(self, message: str, source_type: str = "", source_path: str = "", **kwargs):
        super().__init__(
            message,
            error_code="LOADER_ERROR",
            context={"source_type": source_type, "source_path": source_path, **kwargs.pop("context", {})},
            **kwargs,
        )


class NormalizationError(PygramatticError):
    """Failed to normalize raw data into a Dataset."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="NORMALIZATION_ERROR", **kwargs)


class StorageError(PygramatticError):
    """Storage operation failed (disk full, permission denied, corrupt manifest)."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="STORAGE_ERROR", **kwargs)


class ConversionError(PygramatticError):
    """Data conversion failed."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="CONVERSION_ERROR", **kwargs)


class TemplateError(PygramatticError):
    """Template parsing or rendering failed."""
    def __init__(self, message: str, template_name: str = "", **kwargs):
        super().__init__(
            message,
            error_code="TEMPLATE_ERROR",
            context={"template_name": template_name, **kwargs.pop("context", {})},
            **kwargs,
        )


class ThemeError(PygramatticError):
    """Theme loading or application failed."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="THEME_ERROR", **kwargs)


class ChartError(PygramatticError):
    """Chart rendering failed."""
    def __init__(self, message: str, chart_type: str = "", **kwargs):
        super().__init__(
            message,
            error_code="CHART_ERROR",
            severity=ErrorSeverity.RECOVERABLE,  # Charts failing should not kill the build
            context={"chart_type": chart_type, **kwargs.pop("context", {})},
            **kwargs,
        )


class BuildError(PygramatticError):
    """Report building failed."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="BUILD_ERROR", **kwargs)


class ValidationError(PygramatticError):
    """Report validation found issues."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)


class AIError(PygramatticError):
    """Claude CLI interaction failed."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code="AI_ERROR",
            severity=ErrorSeverity.RETRIABLE,
            **kwargs,
        )


class FeedbackError(PygramatticError):
    """Feedback processing failed."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="FEEDBACK_ERROR", **kwargs)


class OutputError(PygramatticError):
    """Output rendering/writing failed."""
    def __init__(self, message: str, output_format: str = "", **kwargs):
        super().__init__(
            message,
            error_code="OUTPUT_ERROR",
            context={"output_format": output_format, **kwargs.pop("context", {})},
            **kwargs,
        )
```

---

### Task 4.2: Set Up Structured Logging

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/logging/setup.py`

**Description:** Configure `structlog` for consistent, structured logging across all modules.

**Requirements:**
- Module-specific loggers: `pygramattic.loaders`, `pygramattic.builder`, etc.
- Console output with `rich` formatting for CLI usage
- JSON output option for production/CI environments
- Every log message should include: `module`, `timestamp`, `level`
- Pipeline runs should carry a `build_id` for correlation
- Performance logging: ability to time operations

```python
import structlog
from pygramattic_reports.config.settings import LoggingConfig


def setup_logging(config: LoggingConfig) -> None:
    """Configure structured logging for the application.

    Call this once at application startup (in CLI main).

    Args:
        config: Logging configuration from AppConfig.
    """
    processors = [
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
            _name_to_level(config.level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(module: str) -> structlog.BoundLogger:
    """Get a logger for a specific module.

    Usage:
        logger = get_logger("loaders")
        logger.info("Loading file", path="/data/input.csv", format="csv")
    """
    return structlog.get_logger(module=module)


def _name_to_level(name: str) -> int:
    """Convert level name to numeric level."""
    levels = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
    return levels.get(name.upper(), 20)
```

---

### Task 4.3: Create Build Log Model

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/logging/build_log.py`

**Description:** Define a structured build log that is saved alongside each report.

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from pygramattic_reports.models.base import generate_id, now_utc


class BuildLogEntry(BaseModel):
    """A single event in the build log."""
    model_config = ConfigDict(frozen=True)

    timestamp: datetime
    level: str                          # "info", "warning", "error"
    module: str                         # Which module produced this
    message: str
    context: dict = {}


class BuildLog(BaseModel):
    """Structured log of an entire report build run.

    Saved as `build_log.json` alongside the generated report.
    """
    build_id: str
    started_at: datetime
    completed_at: datetime | None = None
    status: str = "in_progress"          # "completed", "completed_with_warnings", "failed"
    entries: list[BuildLogEntry] = []

    # Summary counters
    sections_generated: int = 0
    sections_skipped: int = 0
    ai_calls: int = 0
    ai_failures: int = 0
    charts_generated: int = 0
    charts_failed: int = 0

    def add_entry(self, level: str, module: str, message: str, **context) -> None:
        """Add a log entry."""
        self.entries.append(BuildLogEntry(
            timestamp=now_utc(),
            level=level,
            module=module,
            message=message,
            context=context,
        ))

    def finalize(self, status: str) -> None:
        """Mark the build as complete."""
        self.completed_at = now_utc()
        self.status = status
```

---

### Task 4.4: Create Logging Package Init

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/logging/__init__.py`

```python
"""Logging and build tracking for pygramattic-reports.

Usage:
    from pygramattic_reports.logging import setup_logging, get_logger

    setup_logging(config.logging)
    logger = get_logger("loaders")
    logger.info("Loading file", path="data.csv")
"""
from .setup import setup_logging, get_logger
from .build_log import BuildLog, BuildLogEntry

__all__ = ["setup_logging", "get_logger", "BuildLog", "BuildLogEntry"]
```

---

### Task 4.5: Write Tests for Exceptions and Logging

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_exceptions.py`

**Test cases:**
1. Each exception class can be raised and caught by its parent type
2. Exception context dict is accessible
3. Error severity is set correctly by default for each type
4. `PygramatticError` is the base for all exceptions

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_logging.py`

**Test cases:**
1. `setup_logging` configures structlog without errors
2. `get_logger` returns a bound logger with the module name
3. `BuildLog` can add entries and finalize
4. `BuildLog` serializes to JSON correctly

---

## Dependencies

- **Depends on:** Phase 01 (project scaffold), Phase 02 (models for BuildLog), Phase 03 (config for logging settings)
- **Blocks:** Phase 05+ (all modules use logging and exceptions)

## Acceptance Criteria

1. All exception classes are importable from `pygramattic_reports.exceptions`
2. `setup_logging()` configures structlog and `get_logger()` returns working loggers
3. `BuildLog` tracks build events and serializes to JSON
4. All tests pass
5. Every exception carries `message`, `error_code`, `severity`, and `context`

## References

- PRD Quality Attributes: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 220-225)
- PRD Claude CLI Failure Handling: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 345-347)
