"""Tests for document structure enhancements (Phase 2)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pygramattic_reports.builder.builder import ReportBuilder
from pygramattic_reports.builder.config import BuildConfig
from pygramattic_reports.models import (
    SectionType,
    TemplateSectionSpec,
    TemplateSpec,
    ThemeSpec,
)


class TestDocumentStructureRefactor:
    """Test verification for DocumentMetadata, PageLayout, and CoverPage."""

    @pytest.fixture
    def mock_components(self):
        """Mock components for builder."""
        return {
            "chart_engine": MagicMock(),
            "template_renderer": MagicMock(),
        }

    def test_metadata_extraction(self, mock_components):
        """Verify DocumentMetadata is extracted from TemplateSpec."""
        metadata = {
            "title": "My Report",
            "author": "Alice",
            "version": "2.0",
            "keywords": ["finance", "Q1"],
        }

        template = TemplateSpec(name="test_tmpl", sections=[], metadata=metadata)

        mock_renderer = mock_components["template_renderer"]
        mock_renderer.resolve_template.return_value = []

        config = BuildConfig(
            report_name="test_report",
            template=template,
            theme=ThemeSpec(name="default"),
            datasets={},
        )

        builder = ReportBuilder(**mock_components)
        report, _ = builder.build(config)

        assert report.metadata is not None
        assert report.metadata.title == "My Report"
        assert report.metadata.author == "Alice"
        assert report.metadata.version == "2.0"
        assert report.metadata.keywords == ["finance", "Q1"]

    def test_page_layout_extraction(self, mock_components):
        """Verify PageLayout is extracted."""
        layout = {"orientation": "landscape", "margin_top_inches": 0.5, "page_numbers": False}

        template = TemplateSpec(name="test_tmpl", sections=[], page_layout=layout)

        mock_renderer = mock_components["template_renderer"]
        mock_renderer.resolve_template.return_value = []

        config = BuildConfig(
            report_name="test_report",
            template=template,
            theme=ThemeSpec(name="default"),
            datasets={},
        )

        builder = ReportBuilder(**mock_components)
        report, _ = builder.build(config)

        assert report.page_layout.orientation == "landscape"
        assert report.page_layout.margin_top_inches == 0.5
        assert report.page_layout.page_numbers is False
        # default check
        assert report.page_layout.margin_bottom_inches == 1.0

    def test_cover_page_injection(self, mock_components):
        """Verify Cover Page is injected as the first section."""
        cover_page = {"title": "Front Page", "logo_path": "logo.png"}

        # Regular section
        section = TemplateSectionSpec(type="narrative", content="Hello")

        template = TemplateSpec(name="test_tmpl", sections=[section], cover_page=cover_page)

        mock_renderer = mock_components["template_renderer"]
        mock_renderer.resolve_template.return_value = [section]

        config = BuildConfig(
            report_name="test_report",
            template=template,
            theme=ThemeSpec(name="default"),
            datasets={},
        )

        builder = ReportBuilder(**mock_components)
        report, _ = builder.build(config)

        assert report.cover_page is not None
        assert report.cover_page.title == "Front Page"

        # Verify section injection
        assert len(report.sections) == 2
        assert report.sections[0].section_type == SectionType.COVER_PAGE
        assert report.sections[0].title == "Cover Page"
        assert report.sections[0].metadata["spec"]["title"] == "Front Page"

        # Original section should be second
        assert report.sections[1].content == "Hello"

    def test_table_of_contents_processing(self, mock_components):
        """Verify Table of Contents section is processed."""
        toc_section = TemplateSectionSpec(type="table_of_contents", title="Contents")

        template = TemplateSpec(name="test_tmpl", sections=[toc_section])

        mock_renderer = mock_components["template_renderer"]
        mock_renderer.resolve_template.return_value = [toc_section]

        config = BuildConfig(
            report_name="test_report",
            template=template,
            theme=ThemeSpec(name="default"),
            datasets={},
        )

        builder = ReportBuilder(**mock_components)
        report, _ = builder.build(config)

        assert len(report.sections) == 1
        assert report.sections[0].section_type == SectionType.TABLE_OF_CONTENTS
        assert report.sections[0].title == "Contents"
