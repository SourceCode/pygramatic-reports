"""Chart specification model for pygramattic-reports.

Defines the abstract chart specification that decouples chart definition
from the rendering library.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ChartType(StrEnum):
    """Supported chart types."""

    BAR = "bar"
    HORIZONTAL_BAR = "horizontal_bar"
    STACKED_BAR = "stacked_bar"
    LINE = "line"
    AREA = "area"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    BOX = "box"
    WATERFALL = "waterfall"
    GAUGE = "gauge"
    FUNNEL = "funnel"
    SANKEY = "sankey"
    TREEMAP = "treemap"
    BUBBLE = "bubble"
    RADAR = "radar"
    POLAR = "polar"
    CANDLESTICK = "candlestick"
    OHLC = "ohlc"
    BULLET = "bullet"
    KAGI = "kagi"
    RENKO = "renko"
    POINT_AND_FIGURE = "point_and_figure"
    HEATMAP_GRID = "heatmap_grid"
    MOSAIC = "mosaic"


class ChartRenderer(StrEnum):
    """Available chart rendering backends."""

    MATPLOTLIB = "matplotlib"
    PLOTLY = "plotly"


class ChartFormat(StrEnum):
    """Chart output image formats."""

    PNG = "png"
    SVG = "svg"
    PDF = "pdf"


class AxisSpec(BaseModel):
    """Configuration for a chart axis."""

    model_config = ConfigDict(frozen=True)

    title: str | None = None
    visible: bool = True
    min_value: float | None = None
    max_value: float | None = None
    log_scale: bool = False
    grid: bool = True
    labels: bool = True
    ticks: bool = True
    format: str | None = None  # e.g., "${x:,.0f}" or "{x:.1%}"


class LegendSpec(BaseModel):
    """Configuration for chart legend."""

    model_config = ConfigDict(frozen=True)

    visible: bool = True
    position: str = "best"
    title: str | None = None
    frame: bool = True
    columns: int = 1


class AnnotationSpec(BaseModel):
    """Configuration for chart annotations."""

    model_config = ConfigDict(frozen=True)

    text: str
    x: float | str
    y: float | str
    color: str | None = None
    size: int | None = None


class DataLabelSpec(BaseModel):
    """Configuration for data point labels."""

    model_config = ConfigDict(frozen=True)

    visible: bool = False
    format: str | None = None  # e.g., "{:.1f}%"
    font_size: int | None = None
    color: str | None = None
    position: str | None = None  # "center", "edge", "outside"


class ChartSpec(BaseModel):
    """Abstract specification for a chart.

    This model describes WHAT chart to produce, not HOW to render it.
    The Chart Engine takes a ChartSpec + Dataset + ThemeSpec and produces
    image bytes.

    Attributes:
        chart_type: The type of chart to render.
        title: Chart title.
        x_column: X-axis column name.
        y_columns: List of Y-axis column names.
        dataset_id: Reference to source dataset.
        x_axis: X-axis configuration.
        y_axis: Y-axis configuration.
        secondary_y_axis: Secondary Y-axis configuration.
        legend_spec: Legend configuration.
        annotations: List of annotations.
        data_labels: Data label configuration.
        subplots: List of sub-chart specs for multi-chart layouts.
        width: Chart width in pixels.
        height: Chart height in pixels.
        dpi: Dots per inch.
        renderer: Rendering backend.
        output_format: File format.
        sort_by: Column to sort by.
        limit: Max rows to limit.
        group_by: Column to group by.
        color_override: Palette override.
        background_color: Background color override.
    """

    model_config = ConfigDict(frozen=True)

    chart_type: ChartType
    title: str
    x_column: str
    y_columns: list[str]
    dataset_id: str

    # Axis Configuration
    x_axis: AxisSpec = AxisSpec()
    y_axis: AxisSpec = AxisSpec()
    secondary_y_axis: AxisSpec | None = None

    # Components
    legend_spec: LegendSpec = LegendSpec()
    annotations: list[AnnotationSpec] = []
    data_labels: DataLabelSpec = DataLabelSpec()
    subplots: list[ChartSpec] = []

    # Sizing
    width: int = 800
    height: int = 600
    dpi: int = 150

    # Rendering
    renderer: ChartRenderer = ChartRenderer.MATPLOTLIB
    output_format: ChartFormat = ChartFormat.PNG

    # Data options
    sort_by: str | None = None
    limit: int | None = None
    group_by: str | None = None

    # Theme overrides
    color_override: list[str] | None = None
    background_color: str | None = None

    @property
    def x_label(self) -> str | None:
        """Backward compatibility for x_label."""
        return self.x_axis.title

    @property
    def y_label(self) -> str | None:
        """Backward compatibility for y_label."""
        return self.y_axis.title

    @property
    def legend(self) -> bool:
        """Backward compatibility for legend visibility."""
        return self.legend_spec.visible

    @property
    def legend_position(self) -> str:
        """Backward compatibility for legend position."""
        return self.legend_spec.position
