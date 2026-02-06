"""Typed exception hierarchy for pygramattic-reports.

Every pipeline module has its own exception class. All exceptions carry
structured context (``message``, ``error_code``, ``severity``,
``context``) for consistent error handling and logging.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


class ErrorSeverity(StrEnum):
    """How the pipeline should react to this error.

    Attributes:
        FATAL: Stop the pipeline immediately.
        RECOVERABLE: Skip the affected section, warn, continue.
        RETRIABLE: Retry with backoff, then degrade.
    """

    FATAL = "fatal"
    RECOVERABLE = "recoverable"
    RETRIABLE = "retriable"


class PygramatticError(Exception):
    """Base exception for all pygramattic-reports errors.

    All exceptions carry structured context for logging and debugging.

    Attributes:
        message: Human-readable error description.
        error_code: Machine-readable error code.
        severity: How the pipeline should react.
        context: Additional structured context for debugging.
    """

    def __init__(  # noqa: D107
        self,
        message: str,
        error_code: str = "UNKNOWN",
        severity: ErrorSeverity = ErrorSeverity.FATAL,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.context: dict[str, Any] = context or {}
        super().__init__(message)


class ConfigError(PygramatticError):
    """Configuration is invalid, missing, or unparseable."""

    def __init__(self, message: str, **kwargs: Any) -> None:  # noqa: D107
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)


class LoaderError(PygramatticError):
    """Failed to load data from a source."""

    def __init__(  # noqa: D107
        self,
        message: str,
        source_type: str = "",
        source_path: str = "",
        **kwargs: Any,
    ) -> None:
        ctx: dict[str, Any] = {
            "source_type": source_type,
            "source_path": source_path,
            **kwargs.pop("context", {}),
        }
        super().__init__(message, error_code="LOADER_ERROR", context=ctx, **kwargs)


class NormalizationError(PygramatticError):
    """Failed to normalize raw data into a Dataset."""

    def __init__(self, message: str, **kwargs: Any) -> None:  # noqa: D107
        super().__init__(message, error_code="NORMALIZATION_ERROR", **kwargs)


class StorageError(PygramatticError):
    """Storage operation failed (disk full, permission denied, corrupt manifest)."""

    def __init__(self, message: str, **kwargs: Any) -> None:  # noqa: D107
        super().__init__(message, error_code="STORAGE_ERROR", **kwargs)


class ConversionError(PygramatticError):
    """Data conversion failed."""

    def __init__(self, message: str, **kwargs: Any) -> None:  # noqa: D107
        super().__init__(message, error_code="CONVERSION_ERROR", **kwargs)


class TemplateError(PygramatticError):
    """Template parsing or rendering failed."""

    def __init__(  # noqa: D107
        self,
        message: str,
        template_name: str = "",
        **kwargs: Any,
    ) -> None:
        ctx: dict[str, Any] = {
            "template_name": template_name,
            **kwargs.pop("context", {}),
        }
        super().__init__(message, error_code="TEMPLATE_ERROR", context=ctx, **kwargs)


class ThemeError(PygramatticError):
    """Theme loading or application failed."""

    def __init__(self, message: str, **kwargs: Any) -> None:  # noqa: D107
        super().__init__(message, error_code="THEME_ERROR", **kwargs)


class ChartError(PygramatticError):
    """Chart rendering failed."""

    def __init__(  # noqa: D107
        self,
        message: str,
        chart_type: str = "",
        **kwargs: Any,
    ) -> None:
        ctx: dict[str, Any] = {
            "chart_type": chart_type,
            **kwargs.pop("context", {}),
        }
        super().__init__(
            message,
            error_code="CHART_ERROR",
            severity=ErrorSeverity.RECOVERABLE,
            context=ctx,
            **kwargs,
        )


class BuildError(PygramatticError):
    """Report building failed."""

    def __init__(self, message: str, **kwargs: Any) -> None:  # noqa: D107
        super().__init__(message, error_code="BUILD_ERROR", **kwargs)


class ValidationError(PygramatticError):
    """Report validation found issues."""

    def __init__(self, message: str, **kwargs: Any) -> None:  # noqa: D107
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)


class AIError(PygramatticError):
    """Claude CLI interaction failed."""

    def __init__(self, message: str, **kwargs: Any) -> None:  # noqa: D107
        super().__init__(
            message,
            error_code="AI_ERROR",
            severity=ErrorSeverity.RETRIABLE,
            **kwargs,
        )


class FeedbackError(PygramatticError):
    """Feedback processing failed."""

    def __init__(self, message: str, **kwargs: Any) -> None:  # noqa: D107
        super().__init__(message, error_code="FEEDBACK_ERROR", **kwargs)


class OutputError(PygramatticError):
    """Output rendering/writing failed."""

    def __init__(  # noqa: D107
        self,
        message: str,
        output_format: str = "",
        **kwargs: Any,
    ) -> None:
        ctx: dict[str, Any] = {
            "output_format": output_format,
            **kwargs.pop("context", {}),
        }
        super().__init__(message, error_code="OUTPUT_ERROR", context=ctx, **kwargs)
