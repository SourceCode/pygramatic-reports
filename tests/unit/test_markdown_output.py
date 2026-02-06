"""Tests for the Markdown output adapter (Phase 14)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pygramattic_reports.models import Report, ReportSection, SectionType, ThemeSpec

if TYPE_CHECKING:
    from pathlib import Path
from pygramattic_reports.outputs import MarkdownAdapter

# ---------- Helpers ----------------------------------------------------------


def _make_report(
    sections: list[ReportSection],
    name: str = "Test Report",
) -> Report:
    return Report(
        id="rpt-001",
        name=name,
        sections=sections,
        template_name="test",
        theme_name="test",
        build_timestamp=datetime(2025, 1, 1, tzinfo=UTC),
    )


def _default_theme() -> ThemeSpec:
    return ThemeSpec(name="test")


# ---------- Title rendering --------------------------------------------------


class TestTitleRendering:
    """Title section renders as ``# Title``."""

    def test_title_rendering(self) -> None:
        report = _make_report([
            ReportSection(section_type=SectionType.TITLE, content="My Report"),
        ])
        md = MarkdownAdapter().render(report, _default_theme()).decode()
        assert "# My Report" in md


# ---------- Heading levels ---------------------------------------------------


class TestHeadingLevels:
    """Heading sections use correct ``#`` count."""

    def test_heading_level_2(self) -> None:
        report = _make_report([
            ReportSection(
                section_type=SectionType.HEADING,
                content="Section One", level=2,
            ),
        ])
        md = MarkdownAdapter().render(report, _default_theme()).decode()
        assert "## Section One" in md

    def test_heading_level_3(self) -> None:
        report = _make_report([
            ReportSection(
                section_type=SectionType.HEADING,
                content="Subsection", level=3,
            ),
        ])
        md = MarkdownAdapter().render(report, _default_theme()).decode()
        assert "### Subsection" in md

    def test_heading_level_clamped_to_6(self) -> None:
        report = _make_report([
            ReportSection(
                section_type=SectionType.HEADING,
                content="Deep", level=10,
            ),
        ])
        md = MarkdownAdapter().render(report, _default_theme()).decode()
        assert "###### Deep" in md
        assert "##########" not in md


# ---------- Narrative rendering ----------------------------------------------


class TestNarrativeRendering:
    """Text sections render as paragraphs."""

    def test_narrative_with_title(self) -> None:
        report = _make_report([
            ReportSection(
                section_type=SectionType.NARRATIVE,
                title="Intro",
                content="This is the intro paragraph.",
            ),
        ])
        md = MarkdownAdapter().render(report, _default_theme()).decode()
        assert "## Intro" in md
        assert "This is the intro paragraph." in md

    def test_summary_rendering(self) -> None:
        report = _make_report([
            ReportSection(
                section_type=SectionType.SUMMARY,
                content="Summary text here.",
            ),
        ])
        md = MarkdownAdapter().render(report, _default_theme()).decode()
        assert "Summary text here." in md


# ---------- Data table rendering ---------------------------------------------


class TestDataTableRendering:
    """Table data renders as Markdown table."""

    def test_data_table_rendering(self) -> None:
        report = _make_report([
            ReportSection(
                section_type=SectionType.DATA_TABLE,
                title="Revenue Table",
                table_data={
                    "headers": ["Region", "Revenue"],
                    "rows": [["US", 1500], ["EU", 2300]],
                },
            ),
        ])
        md = MarkdownAdapter().render(report, _default_theme()).decode()
        assert "## Revenue Table" in md
        assert "| Region | Revenue |" in md
        assert "| US | 1500 |" in md
        assert "| EU | 2300 |" in md

    def test_table_has_separator_row(self) -> None:
        report = _make_report([
            ReportSection(
                section_type=SectionType.DATA_TABLE,
                table_data={
                    "headers": ["A", "B"],
                    "rows": [["x", 1]],
                },
            ),
        ])
        md = MarkdownAdapter().render(report, _default_theme()).decode()
        assert "| --- |" in md or "| ---: |" in md

    def test_numeric_alignment(self) -> None:
        report = _make_report([
            ReportSection(
                section_type=SectionType.DATA_TABLE,
                table_data={
                    "headers": ["Name", "Value"],
                    "rows": [["A", 10], ["B", 20]],
                },
            ),
        ])
        md = MarkdownAdapter().render(report, _default_theme()).decode()
        assert "---:" in md  # right-aligned numeric column

    def test_empty_table_data(self) -> None:
        report = _make_report([
            ReportSection(
                section_type=SectionType.DATA_TABLE,
                table_data=None,
            ),
        ])
        md = MarkdownAdapter().render(report, _default_theme()).decode()
        assert "|" not in md


# ---------- Table cell formatting --------------------------------------------


class TestTableFormatting:
    """Table cells are properly escaped."""

    def test_pipe_escape(self) -> None:
        report = _make_report([
            ReportSection(
                section_type=SectionType.DATA_TABLE,
                table_data={
                    "headers": ["Text"],
                    "rows": [["has|pipe"]],
                },
            ),
        ])
        md = MarkdownAdapter().render(report, _default_theme()).decode()
        assert "has\\|pipe" in md

    def test_none_cell(self) -> None:
        report = _make_report([
            ReportSection(
                section_type=SectionType.DATA_TABLE,
                table_data={
                    "headers": ["A"],
                    "rows": [[None]],
                },
            ),
        ])
        md = MarkdownAdapter().render(report, _default_theme()).decode()
        assert "|  |" in md


# ---------- Chart image reference --------------------------------------------


class TestChartImageReference:
    """Chart sections produce ``![](path)`` references."""

    def test_chart_with_media_dir(self, tmp_path: Path) -> None:
        media_dir = tmp_path / "media"
        report = _make_report([
            ReportSection(
                section_type=SectionType.CHART,
                title="Revenue Chart",
                media_bytes=b"\x89PNG fake image data",
                media_type="image/png",
            ),
        ])
        adapter = MarkdownAdapter(media_dir=media_dir)
        md = adapter.render(report, _default_theme()).decode()
        assert "![Revenue Chart]" in md
        assert "chart_000.png" in md

    def test_chart_without_media_dir(self) -> None:
        report = _make_report([
            ReportSection(
                section_type=SectionType.CHART,
                title="My Chart",
                media_bytes=b"\x89PNG data",
                media_type="image/png",
            ),
        ])
        md = MarkdownAdapter().render(report, _default_theme()).decode()
        assert "[Chart: My Chart]" in md


# ---------- Page break -------------------------------------------------------


class TestPageBreak:
    """Page breaks render as ``---``."""

    def test_page_break(self) -> None:
        report = _make_report([
            ReportSection(section_type=SectionType.PAGE_BREAK),
        ])
        md = MarkdownAdapter().render(report, _default_theme()).decode()
        assert "---" in md


# ---------- Full report ------------------------------------------------------


class TestFullReport:
    """Complete report renders all sections in order."""

    def test_full_report(self) -> None:
        report = _make_report([
            ReportSection(
                section_type=SectionType.TITLE, content="Title",
            ),
            ReportSection(
                section_type=SectionType.HEADING,
                content="Section", level=2,
            ),
            ReportSection(
                section_type=SectionType.NARRATIVE,
                content="Some text.",
            ),
            ReportSection(
                section_type=SectionType.DATA_TABLE,
                table_data={
                    "headers": ["A"],
                    "rows": [["x"]],
                },
            ),
            ReportSection(section_type=SectionType.PAGE_BREAK),
        ])
        md = MarkdownAdapter().render(report, _default_theme()).decode()
        lines = md.split("\n")
        title_idx = next(
            i for i, line in enumerate(lines) if "# Title" in line
        )
        heading_idx = next(
            i for i, line in enumerate(lines) if "## Section" in line
        )
        text_idx = next(
            i for i, line in enumerate(lines) if "Some text." in line
        )
        table_idx = next(
            i for i, line in enumerate(lines) if "| A |" in line
        )
        hr_idx = next(i for i, line in enumerate(lines) if line == "---")
        assert title_idx < heading_idx < text_idx < table_idx < hr_idx


# ---------- Save with media --------------------------------------------------


class TestSaveWithMedia:
    """Charts saved to media directory."""

    def test_save_with_media(self, tmp_path: Path) -> None:
        report = _make_report([
            ReportSection(
                section_type=SectionType.CHART,
                title="Chart",
                media_bytes=b"fake-png-data",
                media_type="image/png",
            ),
        ])
        out_path = tmp_path / "report.md"
        media_dir = tmp_path / "media"
        adapter = MarkdownAdapter()
        adapter.save(report, _default_theme(), out_path, media_dir=media_dir)

        assert out_path.exists()
        assert (media_dir / "chart_000.png").exists()
        assert (media_dir / "chart_000.png").read_bytes() == b"fake-png-data"


# ---------- Empty report -----------------------------------------------------


class TestEmptyReport:
    """Empty report produces minimal output."""

    def test_empty_report(self) -> None:
        report = _make_report([])
        md = MarkdownAdapter().render(report, _default_theme()).decode()
        assert md.strip() == ""


# ---------- UTF-8 encoding ---------------------------------------------------


class TestUtf8Encoding:
    """Output is valid UTF-8."""

    def test_utf8_encoding(self) -> None:
        report = _make_report([
            ReportSection(
                section_type=SectionType.TITLE,
                content="Rapport financier \u2014 Q4",
            ),
            ReportSection(
                section_type=SectionType.NARRATIVE,
                content="\u00c9t\u00e9 2024: r\u00e9sultats \u2265 pr\u00e9visions",
            ),
        ])
        raw = MarkdownAdapter().render(report, _default_theme())
        text = raw.decode("utf-8")
        assert "\u2014" in text
        assert "\u2265" in text
        assert "\u00c9t\u00e9" in text


# ---------- Table of contents ------------------------------------------------


class TestTableOfContents:
    """Table of contents renders as placeholder."""

    def test_toc_placeholder(self) -> None:
        report = _make_report([
            ReportSection(section_type=SectionType.TABLE_OF_CONTENTS),
        ])
        md = MarkdownAdapter().render(report, _default_theme()).decode()
        assert "Table of Contents" in md
