"""Tests for the chart engine (Phase 12)."""

from __future__ import annotations

import pandas as pd
import pytest

from pygramattic_reports.charts import ChartEngine, MatplotlibRenderer
from pygramattic_reports.exceptions import ChartError
from pygramattic_reports.models import (
    ChartFormat,
    ChartSpec,
    ChartType,
    ColumnSchema,
    DataType,
    Provenance,
    ThemeSpec,
)
from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.models.dataset import Dataset

# ---------- Helpers ----------------------------------------------------------

_PNG_HEADER = b"\x89PNG\r\n\x1a\n"


def _make_dataset(
    data: dict[str, list[object]],
    schema: list[ColumnSchema],
    name: str = "test_data",
) -> Dataset:
    """Build a Dataset from column data and schema."""
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
    """Create a standard dataset for chart tests."""
    return _make_dataset(
        data={
            "region": ["US", "EU", "APAC", "LATAM"],
            "revenue": [1500, 2300, 890, 650],
            "cost": [800, 1100, 500, 300],
            "growth": [5.2, 3.8, 7.1, 4.5],
        },
        schema=[
            ColumnSchema(name="region", dtype=DataType.STRING),
            ColumnSchema(name="revenue", dtype=DataType.INTEGER),
            ColumnSchema(name="cost", dtype=DataType.INTEGER),
            ColumnSchema(name="growth", dtype=DataType.FLOAT),
        ],
    )


def _default_theme() -> ThemeSpec:
    """Return a minimal default theme."""
    return ThemeSpec(name="test")


def _chart_spec(
    chart_type: ChartType = ChartType.BAR,
    **kwargs: object,
) -> ChartSpec:
    """Create a ChartSpec with sensible defaults."""
    defaults: dict[str, object] = {
        "chart_type": chart_type,
        "title": "Test Chart",
        "x_column": "region",
        "y_columns": ["revenue"],
        "dataset_id": "test",
    }
    defaults.update(kwargs)
    return ChartSpec(**defaults)


# ---------- Chart Rendering Tests --------------------------------------------


class TestBarChartRenders:
    """Test vertical bar chart rendering."""

    def test_bar_chart_renders(self) -> None:
        """Bar chart produces non-empty PNG bytes with valid header."""
        engine = ChartEngine()
        ds = _sample_dataset()
        spec = _chart_spec(ChartType.BAR)
        result = engine.generate(spec, ds, _default_theme())

        assert len(result) > 0
        assert result[:8] == _PNG_HEADER

    def test_bar_chart_multi_y(self) -> None:
        """Bar chart with multiple y columns works."""
        engine = ChartEngine()
        ds = _sample_dataset()
        spec = _chart_spec(ChartType.BAR, y_columns=["revenue", "cost"])
        result = engine.generate(spec, ds, _default_theme())

        assert len(result) > 0
        assert result[:8] == _PNG_HEADER


class TestLineChartRenders:
    """Test line chart rendering."""

    def test_line_chart_renders(self) -> None:
        """Line chart renders successfully."""
        engine = ChartEngine()
        ds = _sample_dataset()
        spec = _chart_spec(ChartType.LINE)
        result = engine.generate(spec, ds, _default_theme())

        assert len(result) > 0
        assert result[:8] == _PNG_HEADER


class TestPieChartRenders:
    """Test pie chart rendering."""

    def test_pie_chart_renders(self) -> None:
        """Pie chart renders successfully."""
        engine = ChartEngine()
        ds = _sample_dataset()
        spec = _chart_spec(ChartType.PIE)
        result = engine.generate(spec, ds, _default_theme())

        assert len(result) > 0
        assert result[:8] == _PNG_HEADER


class TestScatterChartRenders:
    """Test scatter plot rendering."""

    def test_scatter_chart_renders(self) -> None:
        """Scatter plot renders successfully."""
        engine = ChartEngine()
        ds = _sample_dataset()
        spec = _chart_spec(
            ChartType.SCATTER,
            x_column="revenue",
            y_columns=["cost"],
        )
        result = engine.generate(spec, ds, _default_theme())

        assert len(result) > 0
        assert result[:8] == _PNG_HEADER


class TestChartAppliesTheme:
    """Test that theme affects chart output."""

    def test_chart_applies_theme(self) -> None:
        """Different themes produce different outputs."""
        engine = ChartEngine()
        ds = _sample_dataset()
        spec = _chart_spec(ChartType.BAR)

        theme1 = ThemeSpec(name="default")
        theme2 = ThemeSpec(
            name="custom",
            colors={"primary": "#ff0000", "chart_palette": ["#ff0000", "#00ff00"]},
            chart={"title_size": 24, "label_size": 18},
        )

        result1 = engine.generate(spec, ds, theme1)
        result2 = engine.generate(spec, ds, theme2)

        # Both produce valid PNGs
        assert result1[:8] == _PNG_HEADER
        assert result2[:8] == _PNG_HEADER
        # Different themes should produce different bytes
        assert result1 != result2


class TestChartMissingColumn:
    """Test error for missing columns."""

    def test_chart_missing_column(self) -> None:
        """Raises ChartError when a required column is missing."""
        engine = ChartEngine()
        ds = _sample_dataset()
        spec = _chart_spec(
            ChartType.BAR,
            x_column="region",
            y_columns=["nonexistent"],
        )

        with pytest.raises(ChartError, match="Columns not found"):
            engine.generate(spec, ds, _default_theme())


class TestChartEmptyData:
    """Test handling empty DataFrame."""

    def test_chart_empty_data(self) -> None:
        """Handles empty DataFrame gracefully."""
        engine = ChartEngine()
        ds = _make_dataset(
            data={"region": [], "revenue": []},
            schema=[
                ColumnSchema(name="region", dtype=DataType.STRING),
                ColumnSchema(name="revenue", dtype=DataType.INTEGER),
            ],
        )
        spec = _chart_spec(ChartType.BAR)
        # Should not crash — produces a chart with no data
        result = engine.generate(spec, ds, _default_theme())
        assert len(result) > 0


class TestChartSinglePoint:
    """Test handling single data point."""

    def test_chart_single_point(self) -> None:
        """Handles single data point."""
        engine = ChartEngine()
        ds = _make_dataset(
            data={"region": ["US"], "revenue": [1500]},
            schema=[
                ColumnSchema(name="region", dtype=DataType.STRING),
                ColumnSchema(name="revenue", dtype=DataType.INTEGER),
            ],
        )
        spec = _chart_spec(ChartType.BAR)
        result = engine.generate(spec, ds, _default_theme())

        assert len(result) > 0
        assert result[:8] == _PNG_HEADER


class TestChartSvgOutput:
    """Test SVG format output."""

    def test_chart_svg_output(self) -> None:
        """SVG format produces valid output."""
        engine = ChartEngine()
        ds = _sample_dataset()
        spec = _chart_spec(
            ChartType.BAR,
            output_format=ChartFormat.SVG,
        )
        result = engine.generate(spec, ds, _default_theme())

        assert len(result) > 0
        # SVG starts with XML or svg tag
        text = result.decode("utf-8")
        assert "<svg" in text


class TestChartWithSorting:
    """Test data sorting."""

    def test_chart_with_sorting(self) -> None:
        """Data sorting is applied before rendering."""
        engine = ChartEngine()
        ds = _sample_dataset()
        spec = _chart_spec(
            ChartType.BAR,
            sort_by="revenue",
        )
        # Should not raise
        result = engine.generate(spec, ds, _default_theme())
        assert len(result) > 0


class TestChartWithLimit:
    """Test data limiting."""

    def test_chart_with_limit(self) -> None:
        """Data limiting is applied before rendering."""
        engine = ChartEngine()
        ds = _sample_dataset()
        spec = _chart_spec(
            ChartType.BAR,
            limit=2,
        )
        result = engine.generate(spec, ds, _default_theme())
        assert len(result) > 0


class TestChartDeterministic:
    """Test deterministic output."""

    def test_chart_deterministic(self) -> None:
        """Same input produces same output bytes."""
        engine = ChartEngine()
        ds = _sample_dataset()
        spec = _chart_spec(ChartType.BAR)
        theme = _default_theme()

        result1 = engine.generate(spec, ds, theme)
        result2 = engine.generate(spec, ds, theme)

        assert result1 == result2


class TestAdditionalChartTypes:
    """Test remaining chart types render without errors."""

    def test_horizontal_bar(self) -> None:
        """Horizontal bar chart renders."""
        engine = ChartEngine()
        ds = _sample_dataset()
        spec = _chart_spec(ChartType.HORIZONTAL_BAR)
        result = engine.generate(spec, ds, _default_theme())
        assert result[:8] == _PNG_HEADER

    def test_stacked_bar(self) -> None:
        """Stacked bar chart renders."""
        engine = ChartEngine()
        ds = _sample_dataset()
        spec = _chart_spec(
            ChartType.STACKED_BAR,
            y_columns=["revenue", "cost"],
        )
        result = engine.generate(spec, ds, _default_theme())
        assert result[:8] == _PNG_HEADER

    def test_area(self) -> None:
        """Area chart renders."""
        engine = ChartEngine()
        ds = _sample_dataset()
        spec = _chart_spec(ChartType.AREA)
        result = engine.generate(spec, ds, _default_theme())
        assert result[:8] == _PNG_HEADER

    def test_donut(self) -> None:
        """Donut chart renders."""
        engine = ChartEngine()
        ds = _sample_dataset()
        spec = _chart_spec(ChartType.DONUT)
        result = engine.generate(spec, ds, _default_theme())
        assert result[:8] == _PNG_HEADER

    def test_heatmap(self) -> None:
        """Heatmap renders with seaborn."""
        engine = ChartEngine()
        ds = _sample_dataset()
        spec = _chart_spec(
            ChartType.HEATMAP,
            y_columns=["revenue", "cost"],
        )
        result = engine.generate(spec, ds, _default_theme())
        assert result[:8] == _PNG_HEADER

    def test_box(self) -> None:
        """Box plot renders with seaborn."""
        engine = ChartEngine()
        ds = _sample_dataset()
        spec = _chart_spec(
            ChartType.BOX,
            y_columns=["revenue", "cost"],
        )
        result = engine.generate(spec, ds, _default_theme())
        assert result[:8] == _PNG_HEADER

    def test_supported_chart_types(self) -> None:
        """MatplotlibRenderer supports all ChartType values."""
        renderer = MatplotlibRenderer()
        supported = renderer.supported_chart_types()
        for ct in ChartType:
            assert ct.value in supported
