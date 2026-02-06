"""Excel output adapter for pygramattic-reports.

Generates XLSX files using openpyxl.
Renders data tables as worksheets and embeds charts as images.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

try:
    import openpyxl
    from openpyxl.drawing.image import Image as ExcelImage
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

from pygramattic_reports.logging import get_logger
from pygramattic_reports.models import SectionType
from pygramattic_reports.outputs.base import BaseOutputAdapter

if TYPE_CHECKING:
    from pygramattic_reports.models import Report, ThemeSpec

logger = get_logger("outputs.xlsx")


class ExcelAdapter(BaseOutputAdapter):
    """Generates Excel reports."""

    def __init__(self) -> None:
        """Initialize and check dependencies."""
        if not HAS_OPENPYXL:
            raise ImportError(
                "openpyxl is required for Excel output. Install it with: pip install openpyxl"
            )

    def render(self, report: Report, theme: ThemeSpec) -> bytes:
        """Render report to XLSX bytes."""
        wb = openpyxl.Workbook()

        # Remove default sheet
        default_sheet = wb.active
        if default_sheet:
            wb.remove(default_sheet)

        # Create Metadata Sheet
        self._render_metadata_sheet(wb, report)

        # Render Sections
        chart_count = 0
        table_count = 0

        for i, section in enumerate(report.sections):
            if section.section_type == SectionType.DATA_TABLE:
                table_count += 1
                sheet_name = f"Table {table_count}"
                if section.title:
                    # Sanitize sheet name (max 31 chars, no invalid chars)
                    sheet_name = self._sanitize_sheet_name(section.title)

                self._render_table_sheet(wb, sheet_name, section, theme)

            elif section.section_type == SectionType.CHART:
                chart_count += 1
                # Place charts on a dedicated sheet or common sheet?
                # For now, let's put charts on a "Charts" sheet or specific named sheet
                sheet_name = "Charts"
                if sheet_name not in wb.sheetnames:
                    wb.create_sheet(sheet_name)

                ws = wb[sheet_name]
                self._render_chart(ws, section, chart_count)

        # Save to bytes
        from io import BytesIO

        output = BytesIO()
        wb.save(output)
        return output.getvalue()

    def file_extension(self) -> str:
        return ".xlsx"

    def _render_metadata_sheet(self, wb: openpyxl.Workbook, report: Report) -> None:
        """Create a summary sheet with report metadata."""
        ws = wb.create_sheet("Metadata", 0)
        ws.append(["Property", "Value"])
        ws.append(["Report ID", report.id])
        ws.append(["Title", report.name])
        ws.append(["Build Date", report.build_timestamp.isoformat()])
        if report.metadata:
            if report.metadata.author:
                ws.append(["Author", report.metadata.author])
            if report.metadata.version:
                ws.append(["Version", report.metadata.version])

        # Style header
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="333333", end_color="333333", fill_type="solid")

        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill

        # Auto-width
        ws.column_dimensions["A"].width = 20
        ws.column_dimensions["B"].width = 50

    def _render_table_sheet(
        self, wb: openpyxl.Workbook, sheet_name: str, section: Any, theme: ThemeSpec
    ) -> None:
        """Render a data table to a new worksheet."""
        # Handle duplicate sheet names
        original_name = sheet_name
        counter = 1
        while sheet_name in wb.sheetnames:
            sheet_name = f"{original_name[:28]} {counter}"
            counter += 1

        ws = wb.create_sheet(sheet_name)

        if not section.table_data:
            return

        headers = section.table_data.get("headers", [])
        rows = section.table_data.get("rows", [])

        # Add Title
        if section.title:
            ws.append([section.title])
            ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers) or 1)
            title_cell = ws.cell(row=1, column=1)
            title_cell.font = Font(size=14, bold=True)
            title_cell.alignment = Alignment(horizontal="center")
            ws.append([])  # Spacer

        # Add Headers
        ws.append(headers)

        # Add Rows
        for row in rows:
            ws.append(row)

        # Style Table Header
        header_row_idx = 3 if section.title else 1
        header_font = Font(bold=True, color="FFFFFF")
        # Use theme primary color if valid hex, else default
        bg_color = theme.colors.primary.replace("#", "")
        if len(bg_color) != 6:
            bg_color = "4F81BD"

        header_fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type="solid")

        for cell in ws[header_row_idx]:
            cell.font = header_font
            cell.fill = header_fill

        # Auto-adjust column widths (simple estimation)
        for i, col in enumerate(headers):
            # rudimentary width calculation
            max_len = len(str(col))
            if rows:
                # Check first 10 rows
                for r in rows[:10]:
                    if i < len(r):
                        max_len = max(max_len, len(str(r[i])))

            width = min(max_len + 2, 50)  # Cap at 50
            ws.column_dimensions[get_column_letter(i + 1)].width = width

    def _render_chart(self, ws: Any, section: Any, chart_index: int) -> None:
        """Embed chart image into worksheet."""
        if not section.media_bytes:
            return

        from io import BytesIO

        img_stream = BytesIO(section.media_bytes)
        img = ExcelImage(img_stream)

        # Position
        # charts stacked vertically with spacing
        row_pos = 1 + (chart_index - 1) * 20
        cell_addr = f"A{row_pos}"

        ws.add_image(img, cell_addr)

        # Add title above
        if section.title:
            ws[cell_addr] = section.title
            ws[cell_addr].font = Font(bold=True, size=12)

    def _sanitize_sheet_name(self, title: str) -> str:
        """Sanitize string for Excel sheet name."""
        invalid_chars = [":", "\\", "/", "?", "*", "[", "]"]
        for char in invalid_chars:
            title = title.replace(char, "")
        return title[:31]
