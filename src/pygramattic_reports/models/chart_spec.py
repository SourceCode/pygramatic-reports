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


class ChartRenderer(StrEnum):
    """Available chart rendering backends."""

    MATPLOTLIB = "matplotlib"
    PLOTLY = "plotly"


class ChartFormat(StrEnum):
    """Chart output image formats."""

    PNG = "png"
    SVG = "svg"
    PDF = "pdf"


class ChartSpec(BaseModel):
    """Abstract specification for a chart.

    This model describes WHAT chart to produce, not HOW to render it.
    The Chart Engine takes a ChartSpec + Dataset + ThemeSpec and produces
    image bytes.

    Attributes:
        chart_type: The type of chart to render.
        title: Chart title.
        x_column: Column name for the x-axis.
        y_columns: Column names for the y-axis.
        dataset_id: Reference to a Dataset.
        x_label: X-axis label.
        y_label: Y-axis label.
        legend: Whether to show legend.
        legend_position: Matplotlib legend position string.
        width: Chart width in pixels.
        height: Chart height in pixels.
        dpi: Dots per inch for rendering.
        renderer: Which backend to use.
        output_format: Output image format.
        sort_by: Column to sort data by.
        limit: Max data points to show.
        group_by: Grouping column for stacked/grouped charts.
        color_override: Custom color palette.
        background_color: Background color override.
    """

    model_config = ConfigDict(frozen=True)

    chart_type: ChartType
    title: str
    x_column: str
    y_columns: list[str]
    dataset_id: str

    # Optional configuration
    x_label: str | None = None
    y_label: str | None = None
    legend: bool = True
    legend_position: str = "best"

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
