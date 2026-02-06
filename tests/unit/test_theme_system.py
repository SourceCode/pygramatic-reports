"""Tests for the Theme System and HTML Adapter."""

from __future__ import annotations

from pygramattic_reports.models import (
    Report,
    ReportSection,
    SectionType,
    ThemeSpec,
)
from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.outputs.html_adapter import HtmlAdapter
from pygramattic_reports.themes.applicator import ThemeApplicator


class TestThemeSystem:
    def test_css_variable_generation(self):
        theme = ThemeSpec(name="test")
        applicator = ThemeApplicator(theme)
        css_vars = applicator.to_css_variables()

        assert "--color-primary:" in css_vars
        assert "--font-heading:" in css_vars
        assert "--spacing-section:" in css_vars

    def test_css_style_generation(self):
        theme = ThemeSpec(name="test")
        applicator = ThemeApplicator(theme)
        styles = applicator.to_css_styles()

        assert ":root {" in styles
        assert "body {" in styles
        assert ".metric-card {" in styles

    def test_html_render_with_theme(self):
        theme = ThemeSpec(name="test")
        report_section = ReportSection(
            section_type=SectionType.METRIC_CARD, card_data={"label": "Revenue", "value": "$1K"}
        )
        report = Report(
            id=generate_id(),
            name="Test Report",
            sections=[report_section],
            template_name="test",
            theme_name="test",
            build_timestamp=now_utc(),
        )

        adapter = HtmlAdapter()
        html_bytes = adapter.render(report, theme)
        html = html_bytes.decode("utf-8")

        assert "<!DOCTYPE html>" in html
        assert "<style>" in html
        assert ":root {" in html  # CSS injected
        assert 'class="metric-card"' in html
        assert "Revenue" in html
        assert "$1K" in html
