"""Base output adapter for pygramattic-reports.

Defines the abstract interface that all output format adapters implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from pygramattic_reports.models import Report, ThemeSpec


class BaseOutputAdapter(ABC):
    """Abstract output adapter.

    Takes a Report (abstract, format-agnostic) and produces
    format-specific output (Markdown, DOCX, etc.).

    Implementations:

    - :class:`MarkdownAdapter` → ``.md`` file
    - ``DocxAdapter`` → ``.docx`` file (Phase 15)
    - ``XlsxAdapter`` → ``.xlsx`` file (future)
    """

    @abstractmethod
    def render(self, report: Report, theme: ThemeSpec) -> bytes:
        """Render a Report to the output format.

        Args:
            report: The abstract report to render.
            theme: Theme for styling.

        Returns:
            The rendered document as bytes.

        Raises:
            OutputError: If rendering fails.
        """
        ...

    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension for this format (e.g., '.md')."""
        ...

    def save(
        self,
        report: Report,
        theme: ThemeSpec,
        output_path: Path,
    ) -> Path:
        """Render and save the report to a file.

        Args:
            report: The report to render.
            theme: Theme for styling.
            output_path: Where to save the output file.

        Returns:
            Path to the saved file.
        """
        content = self.render(report, theme)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(content)
        return output_path
