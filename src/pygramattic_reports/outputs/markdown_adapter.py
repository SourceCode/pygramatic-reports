"""Markdown output adapter for pygramattic-reports.

Converts an abstract Report into a well-formatted Markdown document
with embedded image references for charts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygramattic_reports.models import SectionType

if TYPE_CHECKING:
    from pathlib import Path

    from pygramattic_reports.models import Report, ReportSection, ThemeSpec

from .base import BaseOutputAdapter


class MarkdownAdapter(BaseOutputAdapter):
    """Renders reports as Markdown documents.

    Produces clean, readable Markdown with:

    - Proper heading levels
    - Formatted data tables
    - Image references for charts
    - Horizontal rules for page breaks
    """

    def __init__(self, media_dir: Path | None = None) -> None:
        """Initialize with optional media directory for chart images.

        Args:
            media_dir: Directory to save chart images. If ``None``,
                chart sections produce a text placeholder instead.
        """
        self._media_dir = media_dir
        self._media_files: list[tuple[str, bytes]] = []

    def render(self, report: Report, theme: ThemeSpec) -> bytes:
        """Render the report as Markdown.

        Args:
            report: The abstract report to render.
            theme: Theme for styling (used for future enhancements).

        Returns:
            UTF-8 encoded Markdown bytes.
        """
        _ = theme  # reserved for future Markdown styling
        lines: list[str] = []

        for i, section in enumerate(report.sections):
            section_md = self._render_section(section, i)
            if section_md is not None:
                lines.append(section_md)
                lines.append("")  # blank line between sections

        return "\n".join(lines).encode("utf-8")

    def file_extension(self) -> str:
        """Return the Markdown file extension."""
        return ".md"

    def save(
        self,
        report: Report,
        theme: ThemeSpec,
        output_path: Path,
        media_dir: Path | None = None,
    ) -> Path:
        """Render and save the report, including media files.

        Args:
            report: The report to render.
            theme: Theme for styling.
            output_path: Where to save the Markdown file.
            media_dir: Where to save chart images. Overrides the
                instance-level media_dir if provided.

        Returns:
            Path to the saved Markdown file.
        """
        if media_dir is not None:
            self._media_dir = media_dir

        if self._media_dir is not None:
            self._media_dir.mkdir(parents=True, exist_ok=True)

        self._media_files = []
        content = self.render(report, theme)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(content)

        if self._media_dir is not None:
            for filename, data in self._media_files:
                (self._media_dir / filename).write_bytes(data)

        return output_path

    # -- Section renderers ----------------------------------------------------

    def _render_section(
        self, section: ReportSection, index: int,
    ) -> str | None:
        """Render a single section to Markdown."""
        st = section.section_type
        text = section.content or section.title or ""

        if st in (SectionType.TITLE, SectionType.HEADING):
            level = 1 if st == SectionType.TITLE else min(section.level, 6)
            return f"{'#' * level} {text}"

        if st in (SectionType.SUMMARY, SectionType.NARRATIVE):
            return self._render_text(section)

        if st == SectionType.DATA_TABLE:
            return self._render_table(section)

        if st in (SectionType.CHART, SectionType.IMAGE):
            return self._render_media(section, index)

        simple_map = {
            SectionType.PAGE_BREAK: "---",
            SectionType.SPACER: "",
            SectionType.TABLE_OF_CONTENTS: "*[Table of Contents placeholder]*",
        }
        return simple_map.get(st, text)

    @staticmethod
    def _render_text(section: ReportSection) -> str:
        """Render a text section (summary / narrative)."""
        heading = f"## {section.title}\n\n" if section.title else ""
        return f"{heading}{section.content or ''}"

    def _render_table(self, section: ReportSection) -> str:
        """Render a data table as a Markdown table."""
        if not section.table_data:
            return ""

        headers: list[str] = section.table_data["headers"]
        rows: list[list[object]] = section.table_data["rows"]

        heading = f"## {section.title}\n\n" if section.title else ""

        header_line = "| " + " | ".join(str(h) for h in headers) + " |"

        sep_parts: list[str] = []
        for col_idx, _h in enumerate(headers):
            if self._is_numeric_column(rows, col_idx):
                sep_parts.append("---:")
            else:
                sep_parts.append("---")
        sep_line = "| " + " | ".join(sep_parts) + " |"

        data_lines: list[str] = []
        for row in rows:
            cells = [self._format_cell(v) for v in row]
            data_lines.append("| " + " | ".join(cells) + " |")

        return heading + "\n".join([header_line, sep_line, *data_lines])

    def _render_media(
        self, section: ReportSection, index: int,
    ) -> str:
        """Render a chart/image as a Markdown image reference."""
        title = section.title or "Chart"
        heading = f"## {section.title}\n\n" if section.title else ""

        if section.media_bytes and self._media_dir is not None:
            ext = (section.media_type or "image/png").split("/")[-1]
            filename = f"chart_{index:03d}.{ext}"
            self._media_files.append((filename, section.media_bytes))
            rel_path = self._media_dir / filename
            return f"{heading}![{title}]({rel_path})"

        return f"{heading}[Chart: {title}]"

    @staticmethod
    def _format_cell(value: object) -> str:
        """Format a table cell value for Markdown."""
        if value is None:
            return ""
        text = str(value)
        return text.replace("|", "\\|")

    @staticmethod
    def _is_numeric_column(
        rows: list[list[object]], col_idx: int,
    ) -> bool:
        """Check if a column contains numeric values."""
        for row in rows:
            if col_idx < len(row) and row[col_idx] is not None:
                return isinstance(row[col_idx], (int, float))
        return False
