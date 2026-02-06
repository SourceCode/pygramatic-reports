"""Tests for layout section processors (Phase 3)."""

from __future__ import annotations

from pygramattic_reports.builder.section_processors import process_layout_section
from pygramattic_reports.models import (
    SectionType,
    TemplateSectionSpec,
)


class TestLayoutProcessors:
    """Test verification for Lists, Callouts, Cards, Code, Quotes, Columns."""

    def test_process_list(self):
        spec = TemplateSectionSpec(type="list", title="My List", items=["A", "B", "C"])
        section, claims = process_layout_section(spec)

        assert section.section_type == SectionType.LIST
        assert section.title == "My List"
        assert section.list_data == ["A", "B", "C"]
        assert claims == []

    def test_process_callout(self):
        spec = TemplateSectionSpec(type="callout", callout_type="warning", content="Caution")
        section, claims = process_layout_section(spec)

        assert section.section_type == SectionType.CALLOUT
        assert section.callout_data["type"] == "warning"
        assert section.callout_data["content"] == "Caution"

    def test_process_metric_card(self):
        spec = TemplateSectionSpec(type="metric_card", metric={"label": "Sales", "value": "100"})
        section, claims = process_layout_section(spec)

        assert section.section_type == SectionType.METRIC_CARD
        assert section.card_data["label"] == "Sales"
        assert section.card_data["value"] == "100"

    def test_process_code_block(self):
        spec = TemplateSectionSpec(type="code_block", language="python", code="print('hi')")
        section, claims = process_layout_section(spec)

        assert section.section_type == SectionType.CODE_BLOCK
        assert section.code_data["language"] == "python"
        assert section.code_data["code"] == "print('hi')"

    def test_process_quote(self):
        spec = TemplateSectionSpec(
            type="quote", content="To be or not to be", quote_author="Shakespeare"
        )
        section, claims = process_layout_section(spec)

        assert section.section_type == SectionType.QUOTE
        assert section.quote_data["text"] == "To be or not to be"
        assert section.quote_data["author"] == "Shakespeare"

    def test_process_columns(self):
        col1 = TemplateSectionSpec(type="narrative", title="Col1")
        col2 = TemplateSectionSpec(type="narrative", title="Col2")

        spec = TemplateSectionSpec(type="columns", columns_spec=[col1, col2])
        section, claims = process_layout_section(spec)

        assert section.section_type == SectionType.COLUMNS
        assert len(section.columns_data) == 2
        assert section.columns_data[0].title == "Col1"
        assert section.columns_data[1].title == "Col2"
