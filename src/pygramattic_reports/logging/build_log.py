"""Build log model for tracking report generation runs.

A ``BuildLog`` is saved alongside each generated report as
``build_log.json``, recording all events, counters, and timing
for the build.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from pygramattic_reports.models.base import now_utc


class BuildLogEntry(BaseModel):
    """A single event in the build log.

    Attributes:
        timestamp: When the event occurred (UTC).
        level: Log level (``"info"``, ``"warning"``, ``"error"``).
        module: Which pipeline module produced this entry.
        message: Human-readable event description.
        context: Additional structured data about the event.
    """

    model_config = ConfigDict(frozen=True)

    timestamp: datetime
    level: str
    module: str
    message: str
    context: dict[str, Any] = {}


class BuildLog(BaseModel):
    """Structured log of an entire report build run.

    Saved as ``build_log.json`` alongside the generated report.

    Attributes:
        build_id: Unique identifier for this build run.
        started_at: When the build started (UTC).
        completed_at: When the build finished (UTC), or ``None``.
        status: Build status (``"in_progress"``, ``"completed"``,
            ``"completed_with_warnings"``, ``"failed"``).
        entries: Ordered list of build log events.
        sections_generated: Number of report sections successfully built.
        sections_skipped: Number of sections that were skipped.
        ai_calls: Number of Claude CLI invocations made.
        ai_failures: Number of Claude CLI invocations that failed.
        charts_generated: Number of charts successfully rendered.
        charts_failed: Number of charts that failed to render.
    """

    build_id: str
    started_at: datetime
    completed_at: datetime | None = None
    status: str = "in_progress"
    entries: list[BuildLogEntry] = []

    sections_generated: int = 0
    sections_skipped: int = 0
    ai_calls: int = 0
    ai_failures: int = 0
    charts_generated: int = 0
    charts_failed: int = 0

    def add_entry(
        self,
        level: str,
        module: str,
        message: str,
        **context: Any,
    ) -> None:
        """Add a log entry to the build log.

        Args:
            level: Log level (``"info"``, ``"warning"``, ``"error"``).
            module: Pipeline module name.
            message: Event description.
            **context: Additional key-value context data.
        """
        self.entries.append(
            BuildLogEntry(
                timestamp=now_utc(),
                level=level,
                module=module,
                message=message,
                context=context,
            ),
        )

    def finalize(self, status: str) -> None:
        """Mark the build as complete.

        Args:
            status: Final build status (e.g. ``"completed"``,
                ``"failed"``).
        """
        self.completed_at = now_utc()
        self.status = status
