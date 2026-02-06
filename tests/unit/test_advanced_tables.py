"""Tests for advanced table features."""

from unittest.mock import Mock

import pandas as pd

from pygramattic_reports.builder.section_processors import process_data_table_section
from pygramattic_reports.models import (
    Dataset,
    Provenance,
    ReportSection,
    SectionType,
    TemplateSectionSpec,
    ThemeSpec,
    now_utc,
)
from pygramattic_reports.outputs.html_adapter import HtmlAdapter


def make_dataset(data: dict) -> Dataset:
    return Dataset(
        id="test",
        name="test",
        dataframe=pd.DataFrame(data),
        schema=[],
        provenance=Mock(spec=Provenance),
        created_at=now_utc(),
    )


class TestAdvancedTables:
    def test_totals_calculation(self):
        """Test that process_data_table_section calculates totals."""
        ds = make_dataset({"item": ["A", "B"], "val": [10.5, 20.0]})
        spec = TemplateSectionSpec(type="data_table", show_totals=True, columns=["item", "val"])

        section, _ = process_data_table_section(spec, ds, 0)

        assert section.table_data is not None
        assert section.table_data["headers"] == ["item", "val"]
        totals = section.table_data["totals"]
        assert len(totals) == 2
        assert totals[0] == "Total"
        assert totals[1] == 30.5

    def test_html_render_with_totals(self):
        """Test HTML rendering includes tfoot."""
        section = ReportSection(
            section_type=SectionType.DATA_TABLE,
            table_data={"headers": ["Col"], "rows": [[1]], "totals": ["Total", 1]},
        )
        adapter = HtmlAdapter()
        theme = ThemeSpec(name="test")

        html_bytes = adapter.render(Mock(sections=[section], name="Test", cover_page=None), theme)
        html = html_bytes.decode("utf-8")

        assert "<tfoot>" in html
        assert "Total" in html

    def test_conditional_formatting(self):
        """Test that negative numbers get 'text-error' class."""
        section = ReportSection(
            section_type=SectionType.DATA_TABLE,
            table_data={"headers": ["Val"], "rows": [[-5.0], [10.0]]},
        )
        adapter = HtmlAdapter()
        theme = ThemeSpec(name="test")

        html_bytes = adapter.render(Mock(sections=[section], name="Test", cover_page=None), theme)
        html = html_bytes.decode("utf-8")

        assert 'class="text-error"' in html
        assert ">-5.00</td>" in html
        assert ">10.00</td>" in html
