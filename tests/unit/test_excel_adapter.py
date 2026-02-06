"""Tests for ExcelAdapter."""

import unittest
from datetime import UTC, datetime
from unittest.mock import MagicMock

from pygramattic_reports.models import DocumentMetadata, Report, ReportSection, SectionType
from pygramattic_reports.outputs.excel_adapter import ExcelAdapter


class TestExcelAdapter(unittest.TestCase):
    def setUp(self):
        self.mock_theme = MagicMock()
        self.mock_theme.colors.primary = "4F81BD"

        self.report = Report(
            id="test-1",
            name="Test Report",
            build_timestamp=datetime.now(UTC),
            metadata=DocumentMetadata(author="Test User"),
            template_name="default",
            theme_name="default",
            sections=[],
        )

    def test_render_metadata(self):
        adapter = ExcelAdapter()
        output = adapter.render(self.report, self.mock_theme)
        self.assertTrue(output.startswith(b"PK"))  # Zip header for xlsx

    def test_render_table(self):
        section = ReportSection(
            section_type=SectionType.DATA_TABLE,
            title="My Table",
            table_data={"headers": ["A", "B"], "rows": [[1, 2], [3, 4]]},
        )
        self.report.sections.append(section)

        adapter = ExcelAdapter()
        output = adapter.render(self.report, self.mock_theme)
        self.assertTrue(len(output) > 0)

    def test_render_chart(self):
        # Create dummy image bytes
        # Minimal PNG header
        dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"

        section = ReportSection(
            section_type=SectionType.CHART, title="My Chart", media_bytes=dummy_png
        )
        self.report.sections.append(section)

        adapter = ExcelAdapter()
        output = adapter.render(self.report, self.mock_theme)
        self.assertTrue(len(output) > 0)
