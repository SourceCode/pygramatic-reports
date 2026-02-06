"""Tests for advanced chart features (Phase 1)."""

from __future__ import annotations

import pandas as pd

from pygramattic_reports.charts import ChartEngine
from pygramattic_reports.models import (
    AnnotationSpec,
    AxisSpec,
    ChartSpec,
    ChartType,
    ColumnSchema,
    DataLabelSpec,
    DataType,
    LegendSpec,
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


def _default_theme() -> ThemeSpec:
    return ThemeSpec(name="test")


def _chart_spec(
    chart_type: ChartType,
    **kwargs: object,
) -> ChartSpec:
    defaults = {
        "chart_type": chart_type,
        "title": "Test Chart",
        "x_column": "category",
        "y_columns": ["value"],
        "dataset_id": "test",
    }
    defaults.update(kwargs)
    return ChartSpec(**defaults)


# ---------- New Chart Types --------------------------------------------------


class TestNewChartTypes:
    """Test rendering of new chart types."""

    def test_waterfall_chart(self) -> None:
        engine = ChartEngine()
        ds = _make_dataset(
            data={
                "category": ["Start", "Sales", "Cost", "Tax", "Net"],
                "value": [0, 1000, -300, -100, 600],
            },
            schema=[
                ColumnSchema(name="category", dtype=DataType.STRING),
                ColumnSchema(name="value", dtype=DataType.INTEGER),
            ],
        )
        spec = _chart_spec(ChartType.WATERFALL)
        result = engine.generate(spec, ds, _default_theme())
        assert result[:8] == _PNG_HEADER

    def test_funnel_chart(self) -> None:
        engine = ChartEngine()
        ds = _make_dataset(
            data={
                "category": ["Leads", "Qualified", "Proposal", "Closed"],
                "value": [1000, 400, 150, 50],
            },
            schema=[
                ColumnSchema(name="category", dtype=DataType.STRING),
                ColumnSchema(name="value", dtype=DataType.INTEGER),
            ],
        )
        spec = _chart_spec(ChartType.FUNNEL)
        result = engine.generate(spec, ds, _default_theme())
        assert result[:8] == _PNG_HEADER

    def test_gauge_chart(self) -> None:
        engine = ChartEngine()
        ds = _make_dataset(
            data={
                "category": ["Score"],
                "value": [75],
                "max": [100],
            },
            schema=[
                ColumnSchema(name="category", dtype=DataType.STRING),
                ColumnSchema(name="value", dtype=DataType.INTEGER),
                ColumnSchema(name="max", dtype=DataType.INTEGER),
            ],
        )
        # Use simple gauge with one value
        spec = _chart_spec(ChartType.GAUGE, y_columns=["value"])
        result = engine.generate(spec, ds, _default_theme())
        assert result[:8] == _PNG_HEADER

    def test_radar_chart(self) -> None:
        engine = ChartEngine()
        ds = _make_dataset(
            data={
                "category": ["Speed", "Power", "Durability", "Range", "Cost"],
                "model_a": [80, 90, 70, 60, 40],
                "model_b": [60, 70, 90, 80, 50],
            },
            schema=[
                ColumnSchema(name="category", dtype=DataType.STRING),
                ColumnSchema(name="model_a", dtype=DataType.INTEGER),
                ColumnSchema(name="model_b", dtype=DataType.INTEGER),
            ],
        )
        spec = _chart_spec(ChartType.RADAR, y_columns=["model_a", "model_b"])
        result = engine.generate(spec, ds, _default_theme())
        assert result[:8] == _PNG_HEADER


# ---------- Advanced Configuration -------------------------------------------


class TestAdvancedConfig:
    """Test axis, legend, and annotation configuration."""

    def test_axis_config(self) -> None:
        engine = ChartEngine()
        ds = _make_dataset(
            data={"category": ["A", "B"], "value": [10, 1000]},
            schema=[
                ColumnSchema(name="category", dtype=DataType.STRING),
                ColumnSchema(name="value", dtype=DataType.INTEGER),
            ],
        )

        # Test log scale and custom title
        spec = _chart_spec(
            ChartType.BAR,
            y_axis=AxisSpec(title="Log Value", log_scale=True, min_value=1, max_value=10000),
        )
        result = engine.generate(spec, ds, _default_theme())
        assert result[:8] == _PNG_HEADER

    def test_legend_config(self) -> None:
        engine = ChartEngine()
        ds = _make_dataset(
            data={"category": ["A", "B", "C"], "val1": [1, 2, 3], "val2": [4, 5, 6]},
            schema=[
                ColumnSchema(name="category", dtype=DataType.STRING),
                ColumnSchema(name="val1", dtype=DataType.INTEGER),
                ColumnSchema(name="val2", dtype=DataType.INTEGER),
            ],
        )

        spec = _chart_spec(
            ChartType.BAR,
            y_columns=["val1", "val2"],
            legend_spec=LegendSpec(position="upper center", columns=2, title="Metrics"),
        )
        result = engine.generate(spec, ds, _default_theme())
        assert result[:8] == _PNG_HEADER

    def test_annotations(self) -> None:
        engine = ChartEngine()
        ds = _make_dataset(
            data={"category": ["A", "B"], "value": [10, 20]},
            schema=[
                ColumnSchema(name="category", dtype=DataType.STRING),
                ColumnSchema(name="value", dtype=DataType.INTEGER),
            ],
        )

        # Numeric coordinates check might be tricky with categorical X,
        # so let's use a scatter plot with numeric X for reliable testing
        ds_num = _make_dataset(
            data={"x": [1, 2, 3], "y": [10, 20, 30]},
            schema=[
                ColumnSchema(name="x", dtype=DataType.INTEGER),
                ColumnSchema(name="y", dtype=DataType.INTEGER),
            ],
        )

        spec = _chart_spec(
            ChartType.SCATTER,
            x_column="x",
            y_columns=["y"],
            annotations=[AnnotationSpec(text="Important Point", x=2, y=20, color="red")],
        )
        result = engine.generate(spec, ds_num, _default_theme())
        assert result[:8] == _PNG_HEADER

    def test_data_labels(self) -> None:
        engine = ChartEngine()
        ds = _make_dataset(
            data={"category": ["A", "B"], "value": [10.5, 20.3]},
            schema=[
                ColumnSchema(name="category", dtype=DataType.STRING),
                ColumnSchema(name="value", dtype=DataType.FLOAT),
            ],
        )

        spec = _chart_spec(
            ChartType.BAR, data_labels=DataLabelSpec(visible=True, format="%.1f", color="black")
        )
        result = engine.generate(spec, ds, _default_theme())
        assert result[:8] == _PNG_HEADER
