"""Tests for the report builder (Phase 13)."""

from __future__ import annotations

import pandas as pd
import pytest

from pygramattic_reports.builder import BuildConfig, ReportBuilder
from pygramattic_reports.charts import ChartEngine
from pygramattic_reports.exceptions import BuildError
from pygramattic_reports.models import (
    SectionSource,
    SectionType,
    TemplateSectionSpec,
    TemplateSpec,
    ThemeSpec,
)
from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.models.dataset import ColumnSchema, Dataset, DataType, Provenance
from pygramattic_reports.templates import TemplateRenderer

# ---------- Helpers ----------------------------------------------------------


def _make_dataset(
    data: dict[str, list[object]],
    schema: list[ColumnSchema],
    name: str = "test_data",
) -> Dataset:
    df = pd.DataFrame(data)
    return Dataset(
        id=generate_id(),
        name=name,
        schema=schema,
        dataframe=df,
        provenance=Provenance(
            source_type="test",
            source_name="test",
            loaded_at=now_utc(),
            normalized_at=now_utc(),
            row_count_raw=len(df),
        ),
    )


def _sample_dataset() -> Dataset:
    return _make_dataset(
        data={
            "region": ["US", "EU", "APAC"],
            "revenue": [1500, 2300, 890],
            "cost": [800, 1100, 500],
        },
        schema=[
            ColumnSchema(name="region", dtype=DataType.STRING),
            ColumnSchema(name="revenue", dtype=DataType.INTEGER),
            ColumnSchema(name="cost", dtype=DataType.INTEGER),
        ],
    )


def _builder() -> ReportBuilder:
    return ReportBuilder(
        chart_engine=ChartEngine(),
        template_renderer=TemplateRenderer(),
    )


def _build_config(
    sections: list[TemplateSectionSpec],
    datasets: dict[str, Dataset] | None = None,
    primary_dataset: str | None = None,
) -> BuildConfig:
    ds = _sample_dataset()
    return BuildConfig(
        report_name="Test Report",
        template=TemplateSpec(name="test", sections=sections),
        theme=ThemeSpec(name="test"),
        datasets=datasets or {"main": ds},
        primary_dataset=primary_dataset or "main",
    )


# ---------- Builder tests ----------------------------------------------------


class TestBuildStaticSections:
    """Test static section rendering."""

    def test_build_static_sections(self) -> None:
        """Title + heading sections render correctly."""
        config = _build_config(
            [
                TemplateSectionSpec(
                    type="title",
                    source=SectionSource.STATIC,
                    content="My Report",
                ),
                TemplateSectionSpec(
                    type="heading",
                    source=SectionSource.STATIC,
                    content="Introduction",
                    level=2,
                ),
            ]
        )
        report, log = _builder().build(config)

        assert len(report.sections) == 2
        assert report.sections[0].section_type == SectionType.TITLE
        assert report.sections[0].content == "My Report"
        assert report.sections[1].section_type == SectionType.HEADING
        assert report.sections[1].content == "Introduction"
        assert log.status == "completed"


class TestBuildDataTableSection:
    """Test data table section."""

    def test_build_data_table_section(self) -> None:
        """Data table contains correct headers and rows."""
        config = _build_config(
            [
                TemplateSectionSpec(
                    type="data_table",
                    source=SectionSource.DATA,
                    title="Revenue Table",
                    dataset="main",
                ),
            ]
        )
        report, _ = _builder().build(config)

        assert len(report.sections) == 1
        section = report.sections[0]
        assert section.section_type == SectionType.DATA_TABLE
        assert section.table_data is not None
        assert section.table_data["headers"] == ["region", "revenue", "cost"]
        assert len(section.table_data["rows"]) == 3


class TestBuildChartSection:
    """Test chart section."""

    def test_build_chart_section(self) -> None:
        """Chart section contains image bytes."""
        config = _build_config(
            [
                TemplateSectionSpec(
                    type="chart",
                    source=SectionSource.CHART,
                    title="Revenue Chart",
                    dataset="main",
                    chart_type="bar",
                    x_column="region",
                    y_columns=["revenue"],
                ),
            ]
        )
        report, _ = _builder().build(config)

        assert len(report.sections) == 1
        section = report.sections[0]
        assert section.section_type == SectionType.CHART
        assert section.media_bytes is not None
        assert len(section.media_bytes) > 0
        assert section.media_type == "image/png"


class TestBuildAiPlaceholder:
    """Test AI placeholder sections."""

    def test_build_ai_placeholder(self) -> None:
        """AI sections get placeholder content."""
        config = _build_config(
            [
                TemplateSectionSpec(
                    type="summary",
                    source=SectionSource.AI_GENERATED,
                    title="Summary",
                    ai_prompt="Summarize the data",
                ),
            ]
        )
        report, _ = _builder().build(config)

        assert len(report.sections) == 1
        section = report.sections[0]
        assert section.section_type == SectionType.SUMMARY
        assert "placeholder" in (section.content or "").lower()
        assert "Summarize the data" in (section.content or "")


class TestBuildFullReport:
    """Test building a complete report."""

    def test_build_full_report(self) -> None:
        """Complete template produces Report with all sections."""
        config = _build_config(
            [
                TemplateSectionSpec(
                    type="title",
                    source=SectionSource.STATIC,
                    content="{{ report_title }}",
                ),
                TemplateSectionSpec(
                    type="data_table",
                    source=SectionSource.DATA,
                    title="Data",
                    dataset="main",
                ),
                TemplateSectionSpec(
                    type="chart",
                    source=SectionSource.CHART,
                    title="Chart",
                    dataset="main",
                    chart_type="bar",
                    x_column="region",
                    y_columns=["revenue"],
                ),
                TemplateSectionSpec(
                    type="summary",
                    source=SectionSource.AI_GENERATED,
                    title="Summary",
                    ai_prompt="Summarize",
                ),
            ]
        )
        report, log = _builder().build(config)

        assert report.name == "Test Report"
        assert len(report.sections) == 4
        assert report.template_name == "test"
        assert report.theme_name == "test"
        assert log.sections_generated == 4
        assert log.status == "completed"


class TestBuildMissingDataset:
    """Test missing dataset reference."""

    def test_build_missing_dataset(self) -> None:
        """Raises BuildError for missing dataset reference."""
        config = _build_config(
            [
                TemplateSectionSpec(
                    type="data_table",
                    source=SectionSource.DATA,
                    title="Data",
                    dataset="nonexistent",
                ),
            ]
        )
        with pytest.raises(BuildError, match="not found"):
            _builder().build(config)


class TestBuildConditionalSectionIncluded:
    """Test conditional section included."""

    def test_build_conditional_section_included(self) -> None:
        """Condition=true results in section being included."""
        config = _build_config(
            [
                TemplateSectionSpec(
                    type="heading",
                    source=SectionSource.STATIC,
                    content="Always",
                    condition="True",
                ),
            ]
        )
        report, _ = _builder().build(config)
        assert len(report.sections) == 1


class TestBuildConditionalSectionExcluded:
    """Test conditional section excluded."""

    def test_build_conditional_section_excluded(self) -> None:
        """Condition=false results in section being excluded."""
        config = _build_config(
            [
                TemplateSectionSpec(
                    type="heading",
                    source=SectionSource.STATIC,
                    content="Never",
                    condition="False",
                ),
            ]
        )
        report, _ = _builder().build(config)
        assert len(report.sections) == 0


class TestBuildLogTracking:
    """Test build log tracking."""

    def test_build_log_tracking(self) -> None:
        """BuildLog records events correctly."""
        config = _build_config(
            [
                TemplateSectionSpec(
                    type="title",
                    source=SectionSource.STATIC,
                    content="Title",
                ),
                TemplateSectionSpec(
                    type="data_table",
                    source=SectionSource.DATA,
                    title="Data",
                    dataset="main",
                ),
            ]
        )
        _, log = _builder().build(config)

        assert log.sections_generated == 2
        assert log.sections_skipped == 0
        assert log.status == "completed"
        assert log.completed_at is not None


class TestNumberClaimsGenerated:
    """Test NumberClaim generation."""

    def test_number_claims_generated(self) -> None:
        """Data table sections generate NumberClaims for numeric cols."""
        config = _build_config(
            [
                TemplateSectionSpec(
                    type="data_table",
                    source=SectionSource.DATA,
                    title="Data",
                    dataset="main",
                ),
            ]
        )
        report, _ = _builder().build(config)

        # revenue (3 rows) + cost (3 rows) = 6 claims
        assert len(report.number_claims) == 6
        assert all(c.section_index == 0 for c in report.number_claims)
        revenues = [c for c in report.number_claims if c.source_column == "revenue"]
        assert len(revenues) == 3


class TestBuildRecoverableError:
    """Test recoverable error handling."""

    def test_build_recoverable_error(self) -> None:
        """Chart failure (recoverable) skips section, continues build."""
        config = _build_config(
            [
                TemplateSectionSpec(
                    type="title",
                    source=SectionSource.STATIC,
                    content="Title",
                ),
                TemplateSectionSpec(
                    type="chart",
                    source=SectionSource.CHART,
                    title="Bad Chart",
                    dataset="main",
                    chart_type="bar",
                    x_column="region",
                    y_columns=["nonexistent_column"],
                ),
                TemplateSectionSpec(
                    type="heading",
                    source=SectionSource.STATIC,
                    content="End",
                ),
            ]
        )
        report, log = _builder().build(config)

        # Chart section should be skipped (ChartError is RECOVERABLE)
        assert len(report.sections) == 2
        assert log.sections_generated == 2
        assert log.sections_skipped == 1
        assert log.status == "completed_with_warnings"
