# Phase 14: Markdown Output Adapter

## Objective

Implement the first output format adapter: Markdown. This converts the abstract `Report` object from the Builder into a well-formatted Markdown document with embedded images.

## Why This Phase Is Fourteenth

With the Builder producing abstract `Report` objects, we need at least one output adapter to produce usable files. Markdown is the simplest output format, requires no binary libraries, and serves as a readable baseline for testing the entire pipeline.

## Tasks

### Task 14.1: Define the Output Adapter Base Class

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/outputs/base.py`

**Description:** Abstract base class that all output format adapters implement.

```python
from abc import ABC, abstractmethod
from pathlib import Path
from pygramattic_reports.models import Report, ThemeSpec


class BaseOutputAdapter(ABC):
    """Abstract output adapter.

    Takes a Report (abstract, format-agnostic) and produces
    format-specific output (Markdown, DOCX, etc.).

    Implementations:
    - MarkdownAdapter → .md file
    - DocxAdapter → .docx file (Phase 15)
    - XlsxAdapter → .xlsx file (future)
    """

    @abstractmethod
    def render(self, report: Report, theme: ThemeSpec) -> bytes:
        """Render a Report to the output format.

        Args:
            report: The abstract report to render
            theme: Theme for styling

        Returns:
            The rendered document as bytes

        Raises:
            OutputError: If rendering fails
        """
        ...

    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension for this format (e.g., '.md', '.docx')."""
        ...

    def save(
        self,
        report: Report,
        theme: ThemeSpec,
        output_path: Path,
        media_dir: Path | None = None,
    ) -> Path:
        """Render and save the report to a file.

        If the report contains media (charts, images), saves them
        to media_dir and adjusts references accordingly.

        Args:
            report: The report to render
            theme: Theme for styling
            output_path: Where to save the output file
            media_dir: Where to save media files (images)

        Returns:
            Path to the saved file
        """
        content = self.render(report, theme)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(content)
        return output_path
```

---

### Task 14.2: Implement the Markdown Output Adapter

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/outputs/markdown_adapter.py`

**Description:** Converts a Report into a well-formatted Markdown document.

**Requirements:**
- Map each `SectionType` to Markdown syntax:
  - `TITLE` → `# Title`
  - `HEADING` → `## Heading` (respect `level`)
  - `SUMMARY` / `NARRATIVE` → paragraph text
  - `DATA_TABLE` → Markdown table (`| col1 | col2 |`)
  - `CHART` / `IMAGE` → `![title](path)` image reference
  - `PAGE_BREAK` → `---` horizontal rule
  - `TABLE_OF_CONTENTS` → placeholder text (Markdown has no native TOC)
- Format data tables with alignment (right-align numbers, left-align text)
- Save chart/image bytes to media directory and reference by relative path
- Handle special characters in content (escape Markdown syntax where needed)
- Output as UTF-8 encoded bytes

```python
from pathlib import Path
from pygramattic_reports.models import Report, ReportSection, SectionType, ThemeSpec
from .base import BaseOutputAdapter


class MarkdownAdapter(BaseOutputAdapter):
    """Renders reports as Markdown documents.

    Produces clean, readable Markdown with:
    - Proper heading levels
    - Formatted data tables
    - Image references for charts
    - Horizontal rules for page breaks
    """

    def __init__(self, media_dir: Path | None = None):
        """
        Args:
            media_dir: Directory to save chart images. If None, charts
                      are referenced as inline base64 (not recommended
                      for large reports).
        """
        self.media_dir = media_dir
        self._media_files: list[tuple[str, bytes]] = []

    def render(self, report: Report, theme: ThemeSpec) -> bytes:
        """Render the report as Markdown."""
        lines: list[str] = []

        for i, section in enumerate(report.sections):
            section_md = self._render_section(section, i)
            if section_md:
                lines.append(section_md)
                lines.append("")  # Blank line between sections

        return "\n".join(lines).encode("utf-8")

    def _render_section(self, section: ReportSection, index: int) -> str:
        """Render a single section to Markdown."""
        match section.section_type:
            case SectionType.TITLE:
                return f"# {section.content}"
            case SectionType.HEADING:
                prefix = "#" * section.level
                return f"{prefix} {section.content or section.title}"
            case SectionType.SUMMARY | SectionType.NARRATIVE:
                heading = f"## {section.title}\n\n" if section.title else ""
                return f"{heading}{section.content or ''}"
            case SectionType.DATA_TABLE:
                return self._render_table(section)
            case SectionType.CHART | SectionType.IMAGE:
                return self._render_media(section, index)
            case SectionType.PAGE_BREAK:
                return "---"
            case SectionType.SPACER:
                return ""
            case _:
                return section.content or ""

    def _render_table(self, section: ReportSection) -> str:
        """Render a data table as a Markdown table."""
        if not section.table_data:
            return ""

        headers = section.table_data["headers"]
        rows = section.table_data["rows"]

        # Build heading
        heading = f"## {section.title}\n\n" if section.title else ""

        # Header row
        header_line = "| " + " | ".join(str(h) for h in headers) + " |"

        # Separator row (with alignment)
        sep_parts = []
        for h in headers:
            sep_parts.append("---")  # Can be enhanced with alignment detection
        sep_line = "| " + " | ".join(sep_parts) + " |"

        # Data rows
        data_lines = []
        for row in rows:
            formatted = [self._format_cell(v) for v in row]
            data_lines.append("| " + " | ".join(formatted) + " |")

        return heading + "\n".join([header_line, sep_line] + data_lines)

    def _render_media(self, section: ReportSection, index: int) -> str:
        """Render a chart/image as a Markdown image reference."""
        if section.media_bytes and self.media_dir:
            # Save to file
            ext = (section.media_type or "image/png").split("/")[-1]
            filename = f"chart_{index:03d}.{ext}"
            self._media_files.append((filename, section.media_bytes))
            filepath = self.media_dir / filename

            heading = f"## {section.title}\n\n" if section.title else ""
            return f"{heading}![{section.title or 'Chart'}]({filepath})"
        return f"[Chart: {section.title or 'Untitled'}]"

    def _format_cell(self, value) -> str:
        """Format a table cell value for Markdown."""
        if value is None:
            return ""
        return str(value)

    def file_extension(self) -> str:
        return ".md"

    def save(self, report, theme, output_path, media_dir=None):
        """Save report and any associated media files."""
        if media_dir:
            self.media_dir = media_dir
            media_dir.mkdir(parents=True, exist_ok=True)

        content = self.render(report, theme)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(content)

        # Save media files
        if media_dir:
            for filename, data in self._media_files:
                (media_dir / filename).write_bytes(data)

        return output_path
```

---

### Task 14.3: Create Outputs Package Init

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/outputs/__init__.py`

```python
"""Output format adapters for pygramattic-reports.

Convert abstract Report objects to format-specific documents.

Usage:
    from pygramattic_reports.outputs import MarkdownAdapter

    adapter = MarkdownAdapter(media_dir=Path("media/"))
    adapter.save(report, theme, Path("report.md"))
"""
from .base import BaseOutputAdapter
from .markdown_adapter import MarkdownAdapter

__all__ = ["BaseOutputAdapter", "MarkdownAdapter"]
```

---

### Task 14.4: Write Markdown Output Tests

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_markdown_output.py`

**Test cases:**
1. `test_title_rendering` -- Title section renders as `# Title`
2. `test_heading_levels` -- Heading sections use correct `#` count
3. `test_narrative_rendering` -- Text sections render as paragraphs
4. `test_data_table_rendering` -- Table data renders as Markdown table
5. `test_table_formatting` -- Table cells are properly escaped
6. `test_chart_image_reference` -- Chart sections produce `![](path)` references
7. `test_page_break` -- Page breaks render as `---`
8. `test_full_report` -- Complete report renders all sections in order
9. `test_save_with_media` -- Charts saved to media directory
10. `test_empty_report` -- Empty report produces minimal output
11. `test_utf8_encoding` -- Output is valid UTF-8

---

## Dependencies

- **Depends on:** Phase 13 (Report model, Builder)
- **Blocks:** Phase 16 (CLI build command needs at least one output)

## Acceptance Criteria

1. `MarkdownAdapter.render()` produces valid Markdown for all section types
2. Data tables render as proper Markdown tables
3. Charts are saved as image files and referenced in the Markdown
4. Output is valid UTF-8
5. All tests pass

## References

- PRD Output Formats: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 196-217)
- PRD Document outputs including MD: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (line 207)
