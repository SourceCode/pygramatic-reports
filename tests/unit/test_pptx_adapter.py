"""Tests for PptxAdapter."""

import unittest
from datetime import UTC, datetime
from unittest.mock import MagicMock

from pygramattic_reports.models import DocumentMetadata, Report, ReportSection, SectionType
from pygramattic_reports.outputs.pptx_adapter import PptxAdapter


class TestPptxAdapter(unittest.TestCase):
    def setUp(self):
        self.mock_theme = MagicMock()
        self.report = Report(
            id="test-1",
            name="Test Report",
            build_timestamp=datetime.now(UTC),
            metadata=DocumentMetadata(author="Test User"),
            template_name="default",
            theme_name="default",
            sections=[],
        )

    def test_render_basic(self):
        adapter = PptxAdapter()
        output = adapter.render(self.report, self.mock_theme)
        self.assertTrue(output.startswith(b"PK"))  # Zip header for pptx

    def test_render_title_section(self):
        section = ReportSection(section_type=SectionType.HEADING, title="Chapter 1")
        self.report.sections.append(section)

        adapter = PptxAdapter()
        output = adapter.render(self.report, self.mock_theme)
        self.assertTrue(len(output) > 0)

    def test_render_narrative(self):
        section = ReportSection(
            section_type=SectionType.NARRATIVE, title="Analysis", content="Some text content."
        )
        self.report.sections.append(section)

        adapter = PptxAdapter()
        output = adapter.render(self.report, self.mock_theme)
        self.assertTrue(len(output) > 0)

    def test_render_list(self):
        section = ReportSection(
            section_type=SectionType.LIST, title="Key Points", list_data=["Point 1", "Point 2"]
        )
        self.report.sections.append(section)

        adapter = PptxAdapter()
        output = adapter.render(self.report, self.mock_theme)
        self.assertTrue(len(output) > 0)

    def test_render_chart(self):
        # Create dummy image bytes
        dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"

        section = ReportSection(
            section_type=SectionType.CHART, title="My Chart", media_bytes=dummy_png
        )
        self.report.sections.append(section)

        adapter = PptxAdapter()
        output = adapter.render(self.report, self.mock_theme)
        self.assertTrue(len(output) > 0)
