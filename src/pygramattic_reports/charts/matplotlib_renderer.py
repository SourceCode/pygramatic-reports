"""Matplotlib/Seaborn chart renderer for pygramattic-reports.

Full chart renderer supporting all standard chart types with
theme-aware styling and headless (Agg backend) rendering.
"""

from __future__ import annotations

import io
import math
import warnings
from typing import TYPE_CHECKING

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patches

mpl.use("Agg")

from pygramattic_reports.exceptions import ChartError
from pygramattic_reports.models import ChartType
from pygramattic_reports.themes import ThemeApplicator

from .base import BaseChartRenderer

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from pygramattic_reports.models import ChartSpec, ThemeSpec

    _ChartMethod = Callable[[ChartSpec, pd.DataFrame, Axes, list[str]], None]


class MatplotlibRenderer(BaseChartRenderer):
    """Chart renderer using matplotlib and seaborn.

    Supports all ``ChartType`` values with theme-aware styling.
    Uses the Agg backend for headless rendering (no display required).
    """

    def render(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        theme: ThemeSpec,
    ) -> bytes:
        """Render a chart to image bytes.

        Args:
            spec: Chart specification.
            data: DataFrame with the required columns.
            theme: Theme for styling.

        Returns:
            Image bytes (PNG, SVG, or PDF).

        Raises:
            ChartError: If rendering fails.
        """
        applicator = ThemeApplicator(theme)
        plt.rcParams.update(applicator.to_matplotlib_params())
        palette = spec.color_override or applicator.get_chart_palette()

        # Handle Polar plots (Radar)
        subplot_kw = {}
        if spec.chart_type == ChartType.RADAR.value:
            subplot_kw = {"projection": "polar"}

        fig, ax = plt.subplots(
            figsize=(spec.width / spec.dpi, spec.height / spec.dpi),
            dpi=spec.dpi,
            subplot_kw=subplot_kw,
        )

        try:
            self._render_chart(spec, data, ax, palette)
            self._draw_annotations(spec, ax, theme)
            self._apply_data_labels(spec, ax, theme)
        except ChartError:
            plt.close(fig)
            raise
        except Exception as exc:
            plt.close(fig)
            msg = f"Failed to render {spec.chart_type.value} chart: {exc}"
            raise ChartError(
                msg,
                chart_type=spec.chart_type.value,
            ) from exc

        self._apply_common_styling(spec, theme, ax)
        plt.tight_layout()

        image_bytes = self._export(fig, spec)
        plt.close(fig)
        return image_bytes

    def supported_chart_types(self) -> list[str]:
        """List all supported chart types.

        Returns:
            List of chart type value strings.
        """
        return [ct.value for ct in ChartType]

    # -- dispatch --------------------------------------------------------------

    def _render_chart(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        ax: Axes,
        palette: list[str],
    ) -> None:
        """Dispatch to chart-type-specific rendering method."""
        renderers: dict[ChartType, _ChartMethod] = {
            # Standard
            ChartType.BAR: self._render_bar,
            ChartType.HORIZONTAL_BAR: self._render_horizontal_bar,
            ChartType.STACKED_BAR: self._render_stacked_bar,
            ChartType.LINE: self._render_line,
            ChartType.AREA: self._render_area,
            ChartType.PIE: self._render_pie,
            ChartType.DONUT: self._render_donut,
            ChartType.SCATTER: self._render_scatter,
            ChartType.HEATMAP: self._render_heatmap,
            ChartType.BOX: self._render_box,
            # New
            ChartType.WATERFALL: self._render_waterfall,
            ChartType.FUNNEL: self._render_funnel,
            ChartType.RADAR: self._render_radar,
            ChartType.GAUGE: self._render_gauge,
        }
        render_fn = renderers.get(spec.chart_type)
        if render_fn is None:
            # Fallback for unimplemented types
            msg = f"Unsupported chart type: {spec.chart_type.value}"
            raise ChartError(msg, chart_type=spec.chart_type.value)
        render_fn(spec, data, ax, palette)

    # -- chart type implementations -------------------------------------------

    def _render_bar(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        ax: Axes,
        palette: list[str],
    ) -> None:
        x = data[spec.x_column]
        x_pos = np.arange(len(x))
        width = 0.8 / len(spec.y_columns)
        for i, col in enumerate(spec.y_columns):
            offset = (i - len(spec.y_columns) / 2 + 0.5) * width
            color = palette[i % len(palette)]
            ax.bar(
                x_pos + offset,
                data[col],
                width=width,
                label=col,
                color=color,
            )
        ax.set_xticks(x_pos)
        ax.set_xticklabels(x, rotation=45, ha="right")

    def _render_horizontal_bar(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        ax: Axes,
        palette: list[str],
    ) -> None:
        x = data[spec.x_column]
        y_pos = np.arange(len(x))
        bar_height = 0.8 / len(spec.y_columns)
        for i, col in enumerate(spec.y_columns):
            offset = (i - len(spec.y_columns) / 2 + 0.5) * bar_height
            color = palette[i % len(palette)]
            ax.barh(
                y_pos + offset,
                data[col],
                height=bar_height,
                label=col,
                color=color,
            )
        ax.set_yticks(y_pos)
        ax.set_yticklabels(x)

    def _render_stacked_bar(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        ax: Axes,
        palette: list[str],
    ) -> None:
        x = data[spec.x_column]
        x_pos = np.arange(len(x))
        bottom = np.zeros(len(x))
        for i, col in enumerate(spec.y_columns):
            values = data[col].to_numpy(dtype=float)
            color = palette[i % len(palette)]
            ax.bar(
                x_pos,
                values,
                bottom=bottom,
                label=col,
                color=color,
            )
            bottom += values
        ax.set_xticks(x_pos)
        ax.set_xticklabels(x, rotation=45, ha="right")

    def _render_line(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        ax: Axes,
        palette: list[str],
    ) -> None:
        x = data[spec.x_column]
        for i, col in enumerate(spec.y_columns):
            color = palette[i % len(palette)]
            ax.plot(x, data[col], label=col, color=color)

    def _render_area(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        ax: Axes,
        palette: list[str],
    ) -> None:
        x = data[spec.x_column]
        for i, col in enumerate(spec.y_columns):
            color = palette[i % len(palette)]
            ax.fill_between(
                x,
                data[col],
                alpha=0.5,
                label=col,
                color=color,
            )
            ax.plot(x, data[col], color=color)

    def _render_pie(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        ax: Axes,
        palette: list[str],
    ) -> None:
        labels = data[spec.x_column].tolist()
        values = data[spec.y_columns[0]]
        colors = palette[: len(labels)]
        ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            startangle=90,
        )
        ax.set_aspect("equal")

    def _render_donut(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        ax: Axes,
        palette: list[str],
    ) -> None:
        labels = data[spec.x_column].tolist()
        values = data[spec.y_columns[0]]
        colors = palette[: len(labels)]
        ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            startangle=90,
            pctdistance=0.85,
        )
        centre = patches.Circle((0, 0), 0.70, fc="white")
        ax.add_artist(centre)
        ax.set_aspect("equal")

    def _render_scatter(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        ax: Axes,
        palette: list[str],
    ) -> None:
        for i, col in enumerate(spec.y_columns):
            color = palette[i % len(palette)]
            ax.scatter(
                data[spec.x_column],
                data[col],
                label=col,
                color=color,
            )

    def _render_heatmap(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        ax: Axes,
        palette: list[str],  # noqa: ARG002
    ) -> None:
        import seaborn as sns  # noqa: PLC0415

        numeric_cols = [c for c in spec.y_columns if c in data.columns]
        if not numeric_cols:
            msg = "Heatmap requires numeric y_columns"
            raise ChartError(msg, chart_type="heatmap")
        pivot_data = data.set_index(spec.x_column)[numeric_cols]
        sns.heatmap(
            pivot_data,
            ax=ax,
            annot=True,
            fmt=".1f",
            cmap="YlOrRd",
        )

    def _render_box(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        ax: Axes,
        palette: list[str],
    ) -> None:
        import seaborn as sns  # noqa: PLC0415

        plot_data = data[spec.y_columns]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            warnings.simplefilter("ignore", PendingDeprecationWarning)
            sns.boxplot(
                data=plot_data,
                ax=ax,
                palette=palette[: len(spec.y_columns)],
            )

    def _render_waterfall(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        ax: Axes,
        palette: list[str],
    ) -> None:
        """Render a waterfall chart."""
        y_col = spec.y_columns[0]
        x_col = spec.x_column

        # Calculate deltas and running totals
        values = data[y_col].to_numpy(dtype=float)
        labels = data[x_col].tolist()

        # Insert starting point if needed, usually waterfall starts at 0
        blank = np.zeros(len(values))
        # Running sum (cumulative), shifted
        cumsum = np.cumsum(values)
        blank[1:] = cumsum[:-1]

        # Determine colors: Green for positive, Red for negative
        colors = []
        for val in values:
            if val >= 0:
                colors.append(palette[0] if len(palette) > 0 else "g")
            else:
                colors.append(palette[1] if len(palette) > 1 else "r")

        # Plot
        ax.bar(range(len(values)), values, bottom=blank, color=colors, tick_label=labels)
        ax.tick_params(axis="x", rotation=45)

    def _render_funnel(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        ax: Axes,
        palette: list[str],
    ) -> None:
        """Render a funnel chart (centered horizontal bar)."""
        y_col = spec.y_columns[0]
        x_col = spec.x_column

        values = data[y_col][::-1]  # Reverse for top-down
        labels = data[x_col][::-1]

        y_pos = np.arange(len(values))
        values_array = np.array(values)

        # Center bars
        max_val = max(values_array)
        left = (max_val - values_array) / 2.0

        for i, (val, l_off) in enumerate(zip(values_array, left)):
            # Convert label to string in case it's numeric/datetime
            lbl = str(labels.iloc[i]) if hasattr(labels, "iloc") else str(labels[i])
            ax.barh(y_pos[i], val, left=l_off, color=palette[i % len(palette)], label=lbl)
            # Add label in center
            ax.text(
                max_val / 2.0,
                y_pos[i],
                f"{lbl}: {val}",
                ha="center",
                va="center",
                color="white",
                fontweight="bold",
            )

        ax.set_yticks([])
        ax.set_xlim(0, max_val)

    def _render_radar(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        ax: Axes,
        palette: list[str],
    ) -> None:
        """Render a radar/spider chart."""
        # X column = categories (angles)
        # Y columns = series (radii)

        categories = data[spec.x_column].tolist()
        N = len(categories)

        # Compute angles (one per category, plus wrap around)
        angles = [n / float(N) * 2 * math.pi for n in range(N)]
        angles += angles[:1]  # Close the loop

        for i, col in enumerate(spec.y_columns):
            values = data[col].tolist()
            values += values[:1]  # Close the loop

            color = palette[i % len(palette)]
            ax.plot(angles, values, color=color, linewidth=2, linestyle="solid", label=col)
            ax.fill(angles, values, color=color, alpha=0.1)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)

    def _render_gauge(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        ax: Axes,
        palette: list[str],
    ) -> None:
        """Render a simple gauge/speedometer."""
        # Use first Y value as current value, second Y (optional) as max
        val = data[spec.y_columns[0]].iloc[0]
        max_val = 100.0
        if len(spec.y_columns) > 1:
            max_val = float(data[spec.y_columns[1]].iloc[0])
        elif spec.y_axis.max_value:
            max_val = spec.y_axis.max_value

        pct = min(max(val / max_val, 0.0), 1.0)

        # Half donut
        ax.pie(
            [pct, 1.0 - pct],
            colors=[palette[0], "#e0e0e0"],
            startangle=180,
            counterclock=False,
            wedgeprops={"width": 0.4},
            radius=1,
        )
        # Clip to top half
        ax.text(0, -0.2, f"{val}", ha="center", fontsize=20, fontweight="bold")
        ax.set_ylim(-0.1, 1.1)

    # -- common styling --------------------------------------------------------

    def _apply_common_styling(
        self,
        spec: ChartSpec,
        theme: ThemeSpec,
        ax: Axes,
    ) -> None:
        """Apply shared styling using the new AxisSpec and LegendSpec."""
        ax.set_title(
            spec.title,
            fontsize=theme.chart.title_size,
            pad=12,
        )

        # X-Axis configuration
        if spec.x_axis.visible:
            ax.set_xlabel(
                spec.x_axis.title or spec.x_column,
                fontsize=theme.chart.label_size,
            )
            if spec.x_axis.min_value is not None:
                ax.set_xlim(left=spec.x_axis.min_value)
            if spec.x_axis.max_value is not None:
                ax.set_xlim(right=spec.x_axis.max_value)
            if spec.x_axis.log_scale:
                ax.set_xscale("log")

            ax.grid(spec.x_axis.grid, axis="x", alpha=0.3)
        else:
            ax.xaxis.set_visible(False)

        # Y-Axis configuration
        if spec.y_axis.visible:
            # Determine label
            y_label = spec.y_axis.title
            if not y_label and len(spec.y_columns) == 1:
                y_label = spec.y_columns[0]

            if y_label:
                ax.set_ylabel(y_label, fontsize=theme.chart.label_size)

            if spec.y_axis.min_value is not None:
                ax.set_ylim(bottom=spec.y_axis.min_value)
            if spec.y_axis.max_value is not None:
                ax.set_ylim(top=spec.y_axis.max_value)
            if spec.y_axis.log_scale:
                ax.set_yscale("log")

            ax.grid(spec.y_axis.grid, axis="y", alpha=0.3)
        else:
            ax.yaxis.set_visible(False)

        # Legend configuration
        _no_legend_types = (
            ChartType.PIE,
            ChartType.DONUT,
            ChartType.HEATMAP,
            ChartType.BOX,
            ChartType.GAUGE,
            ChartType.FUNNEL,
            ChartType.WATERFALL,
        )
        if spec.legend_spec.visible and spec.chart_type not in _no_legend_types:
            # If explicit position or columns provided
            ax.legend(
                loc=spec.legend_spec.position,
                ncol=spec.legend_spec.columns,
                frameon=spec.legend_spec.frame,
            )

    def _draw_annotations(
        self,
        spec: ChartSpec,
        ax: Axes,
        theme: ThemeSpec,
    ) -> None:
        """Draw annotations from spec."""
        for note in spec.annotations:
            color = note.color or theme.chart.annotation_color
            # Check if coordinates are numeric
            try:
                x = float(note.x)
                y = float(note.y)
                ax.text(
                    x,
                    y,
                    note.text,
                    color=color,
                    fontsize=theme.chart.label_size,
                )
            except ValueError:
                # String coordinates (categorical)
                # This needs proper transformation but basic support:
                ax.text(
                    float(note.x),
                    float(note.y),
                    note.text,
                    color=color,
                    fontsize=theme.chart.label_size,
                )

    def _apply_data_labels(
        self,
        spec: ChartSpec,
        ax: Axes,
        theme: ThemeSpec,
    ) -> None:
        """Apply data labels if enabled."""
        if not spec.data_labels.visible:
            return

        fmt = spec.data_labels.format or "%.2f"
        size = spec.data_labels.font_size or theme.chart.data_label_size
        color = spec.data_labels.color or theme.chart.data_label_color

        for container in ax.containers:
            # seaborn heatmap returns QuadMesh, not Container with bars
            if hasattr(container, "patches") or hasattr(container, "datavalues"):
                from typing import cast

                from matplotlib.container import BarContainer

                ax.bar_label(
                    cast("BarContainer", container),
                    fmt=fmt,
                    padding=3,
                    fontsize=size,
                    color=color,
                )

    # -- export ----------------------------------------------------------------

    @staticmethod
    def _export(fig: Figure, spec: ChartSpec) -> bytes:
        """Export figure to bytes in the requested format."""
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format=spec.output_format.value,
            dpi=spec.dpi,
            bbox_inches="tight",
        )
        buf.seek(0)
        return buf.read()
