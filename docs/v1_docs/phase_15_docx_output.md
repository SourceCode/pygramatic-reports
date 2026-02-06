# Phase 15: DOCX Output Adapter

## Objective

Implement the DOCX (Word document) output adapter using `python-docx`. This converts the abstract `Report` object into a professionally styled Word document with tables, charts, and proper formatting.

## Why This Phase Is Fifteenth

DOCX is the most important document output format for business users. With the Markdown adapter working (Phase 14), the pattern for output adapters is established. The DOCX adapter adds rich formatting, embedded images, and theme-driven styling.

## Tasks

### Task 15.1: Implement the DOCX Output Adapter

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/outputs/docx_adapter.py`

**Description:** Converts a Report into a styled Word document using `python-docx`.

**Requirements:**
- Map each `SectionType` to DOCX elements:
  - `TITLE` → Document title paragraph with Title style
  - `HEADING` → Heading paragraph (Heading 1, 2, 3 based on `level`)
  - `SUMMARY` / `NARRATIVE` → Normal paragraph(s)
  - `DATA_TABLE` → Word table with header row styling
  - `CHART` / `IMAGE` → Inline picture
  - `PAGE_BREAK` → Page break
  - `SPACER` → Empty paragraph
- Apply theme styling:
  - Font family and sizes from ThemeSpec
  - Colors for headings and body text
  - Table styling (header row color, alternating row shading)
  - Page margins from SpacingSpec
- Handle long text: split into paragraphs on double-newline
- Handle chart images: embed as inline pictures with proper sizing
- Produce valid `.docx` files that open correctly in Microsoft Word and LibreOffice

```python
import io
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from pygramattic_reports.models import Report, ReportSection, SectionType, ThemeSpec
from pygramattic_reports.themes import ThemeApplicator
from .base import BaseOutputAdapter


class DocxAdapter(BaseOutputAdapter):
    """Renders reports as DOCX (Word) documents.

    Produces professional Word documents with:
    - Themed heading styles
    - Formatted data tables with header styling
    - Embedded chart images
    - Consistent font and color theming
    - Proper page margins
    """

    def render(self, report: Report, theme: ThemeSpec) -> bytes:
        """Render the report as a DOCX document."""
        doc = Document()
        applicator = ThemeApplicator(theme)
        styles = applicator.to_docx_styles()

        # Configure page layout
        self._setup_page(doc, theme)

        # Render each section
        for section in report.sections:
            self._render_section(doc, section, theme, styles)

        # Export to bytes
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return buf.read()

    def _setup_page(self, doc: Document, theme: ThemeSpec) -> None:
        """Configure page margins and default styles."""
        section = doc.sections[0]
        margin = Inches(theme.spacing.page_margin_inches)
        section.top_margin = margin
        section.bottom_margin = margin
        section.left_margin = margin
        section.right_margin = margin

    def _render_section(self, doc, section, theme, styles):
        """Dispatch section rendering by type."""
        match section.section_type:
            case SectionType.TITLE:
                self._add_title(doc, section, styles)
            case SectionType.HEADING:
                self._add_heading(doc, section, styles)
            case SectionType.SUMMARY | SectionType.NARRATIVE:
                self._add_text(doc, section, styles)
            case SectionType.DATA_TABLE:
                self._add_table(doc, section, theme, styles)
            case SectionType.CHART | SectionType.IMAGE:
                self._add_image(doc, section, styles)
            case SectionType.PAGE_BREAK:
                doc.add_page_break()
            case SectionType.SPACER:
                doc.add_paragraph("")

    def _add_title(self, doc, section, styles):
        """Add a document title."""
        p = doc.add_heading(section.content or "", level=0)
        # Apply theme font and color
        ...

    def _add_heading(self, doc, section, styles):
        """Add a section heading."""
        text = section.content or section.title or ""
        level = min(section.level, 4)  # DOCX supports heading levels 0-4
        doc.add_heading(text, level=level)

    def _add_text(self, doc, section, styles):
        """Add narrative/summary text."""
        if section.title:
            doc.add_heading(section.title, level=2)

        if section.content:
            # Split on double newlines for multiple paragraphs
            paragraphs = section.content.split("\n\n")
            for para_text in paragraphs:
                p = doc.add_paragraph(para_text.strip())
                # Apply body font
                for run in p.runs:
                    run.font.name = styles["fonts"]["body"]
                    run.font.size = Pt(styles["sizes"]["body"])

    def _add_table(self, doc, section, theme, styles):
        """Add a data table with header styling."""
        if section.title:
            doc.add_heading(section.title, level=2)

        if not section.table_data:
            return

        headers = section.table_data["headers"]
        rows = section.table_data["rows"]

        table = doc.add_table(rows=1 + len(rows), cols=len(headers))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Header row
        header_color = RGBColor.from_string(theme.colors.primary.lstrip("#"))
        for i, header in enumerate(headers):
            cell = table.rows[0].cells[i]
            cell.text = str(header)
            # Style header: bold, white text, primary color background
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)
                    run.font.size = Pt(styles["sizes"]["body"])

        # Data rows
        for row_idx, row_data in enumerate(rows):
            for col_idx, value in enumerate(row_data):
                cell = table.rows[row_idx + 1].cells[col_idx]
                cell.text = str(value) if value is not None else ""

    def _add_image(self, doc, section, styles):
        """Add a chart or image."""
        if section.title:
            doc.add_heading(section.title, level=2)

        if section.media_bytes:
            stream = io.BytesIO(section.media_bytes)
            doc.add_picture(stream, width=Inches(6))
            # Center the image
            last_paragraph = doc.paragraphs[-1]
            last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def file_extension(self) -> str:
        return ".docx"
```

---

### Task 15.2: Implement XLSX Output Adapter

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/outputs/xlsx_adapter.py`

**Description:** Exports dataset data (specifically data tables from reports) as Excel spreadsheets.

**Requirements:**
- Use `openpyxl` to create workbooks
- Create one sheet per data table in the report
- Apply header styling (bold, colored background from theme)
- Auto-size columns
- Format numbers, dates appropriately
- This is primarily for data export, not full report rendering

```python
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from pygramattic_reports.models import Report, SectionType, ThemeSpec
from .base import BaseOutputAdapter


class XlsxAdapter(BaseOutputAdapter):
    """Renders report data tables as Excel spreadsheets."""

    def render(self, report: Report, theme: ThemeSpec) -> bytes:
        """Render data tables from the report as XLSX."""
        wb = Workbook()
        ws = wb.active

        # Find all data table sections
        tables = [s for s in report.sections if s.section_type == SectionType.DATA_TABLE]

        if not tables:
            ws.title = "No Data"
            ws["A1"] = "No data tables in this report"
        else:
            for i, table_section in enumerate(tables):
                if i == 0:
                    ws.title = table_section.title or "Data"
                else:
                    ws = wb.create_sheet(title=table_section.title or f"Sheet{i+1}")

                self._write_table(ws, table_section, theme)

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf.read()

    def _write_table(self, ws, section, theme):
        """Write a data table to a worksheet."""
        if not section.table_data:
            return

        headers = section.table_data["headers"]
        rows = section.table_data["rows"]

        # Write headers with styling
        header_fill = PatternFill(
            start_color=theme.colors.primary.lstrip("#"),
            end_color=theme.colors.primary.lstrip("#"),
            fill_type="solid",
        )
        header_font = Font(bold=True, color="FFFFFF")

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font

        # Write data rows
        for row_idx, row_data in enumerate(rows, 2):
            for col_idx, value in enumerate(row_data, 1):
                ws.cell(row=row_idx, column=col_idx, value=value)

    def file_extension(self) -> str:
        return ".xlsx"
```

---

### Task 15.3: Update Outputs Package Init

**File to update:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/outputs/__init__.py`

```python
"""Output format adapters for pygramattic-reports.

Usage:
    from pygramattic_reports.outputs import MarkdownAdapter, DocxAdapter, XlsxAdapter
"""
from .base import BaseOutputAdapter
from .markdown_adapter import MarkdownAdapter
from .docx_adapter import DocxAdapter
from .xlsx_adapter import XlsxAdapter

__all__ = ["BaseOutputAdapter", "MarkdownAdapter", "DocxAdapter", "XlsxAdapter"]
```

---

### Task 15.4: Implement Output Registry

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/outputs/registry.py`

**Description:** Registry that maps format names to output adapters.

```python
from .base import BaseOutputAdapter
from .markdown_adapter import MarkdownAdapter
from .docx_adapter import DocxAdapter
from .xlsx_adapter import XlsxAdapter


class OutputRegistry:
    """Registry of output format adapters.

    Usage:
        registry = create_default_output_registry()
        adapter = registry.get_adapter("docx")
    """

    def __init__(self):
        self._adapters: dict[str, BaseOutputAdapter] = {}

    def register(self, format_name: str, adapter: BaseOutputAdapter):
        self._adapters[format_name] = adapter

    def get_adapter(self, format_name: str) -> BaseOutputAdapter:
        adapter = self._adapters.get(format_name)
        if adapter is None:
            available = ", ".join(self._adapters.keys())
            raise ValueError(f"No adapter for format '{format_name}'. Available: {available}")
        return adapter

    def available_formats(self) -> list[str]:
        return list(self._adapters.keys())


def create_default_output_registry() -> OutputRegistry:
    registry = OutputRegistry()
    registry.register("md", MarkdownAdapter())
    registry.register("markdown", MarkdownAdapter())
    registry.register("docx", DocxAdapter())
    registry.register("xlsx", XlsxAdapter())
    return registry
```

---

### Task 15.5: Write DOCX and XLSX Output Tests

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_docx_output.py`

**Test cases:**
1. `test_docx_title` -- Title renders as heading level 0
2. `test_docx_headings` -- Headings use correct levels
3. `test_docx_narrative` -- Text renders as paragraphs
4. `test_docx_data_table` -- Table renders with headers and data
5. `test_docx_chart_embedded` -- Chart image is embedded
6. `test_docx_page_break` -- Page break inserts correctly
7. `test_docx_valid_file` -- Output opens with python-docx (roundtrip test)
8. `test_docx_theme_styling` -- Theme fonts and colors applied
9. `test_xlsx_data_table` -- XLSX contains correct data
10. `test_xlsx_header_styling` -- Headers are styled
11. `test_xlsx_multiple_tables` -- Multiple tables create multiple sheets
12. `test_output_registry` -- Registry returns correct adapters

---

## Dependencies

- **Depends on:** Phase 13 (Report model), Phase 11 (ThemeApplicator for DOCX styles)
- **Blocks:** Phase 16 (CLI build command)

## Acceptance Criteria

1. `DocxAdapter.render()` produces valid DOCX files that open in Word
2. DOCX contains correctly formatted titles, headings, tables, and images
3. Theme styling is applied (fonts, colors, spacing)
4. `XlsxAdapter.render()` produces valid XLSX files
5. `OutputRegistry` routes format names to correct adapters
6. All tests pass

## References

- PRD Output Formats: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 196-217)
- PRD DOCX output: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (line 204)
- PRD Templates output-agnostic: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (line 104)
