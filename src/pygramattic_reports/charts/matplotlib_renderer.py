"""Matplotlib/Seaborn chart renderer for pygramattic-reports.

Full chart renderer supporting all standard chart types with
theme-aware styling and headless (Agg backend) rendering.
"""

from __future__ import annotations

import io
import warnings
from typing import TYPE_CHECKING

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

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

    _ChartMethod = Callable[
        [ChartSpec, pd.DataFrame, Axes, list[str]], None
    ]


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

        fig, ax = plt.subplots(
            figsize=(spec.width / spec.dpi, spec.height / spec.dpi),
            dpi=spec.dpi,
        )

        try:
            self._render_chart(spec, data, ax, palette)
        except ChartError:
            plt.close(fig)
            raise
        except Exception as exc:
            plt.close(fig)
            msg = f"Failed to render {spec.chart_type.value} chart: {exc}"
            raise ChartError(
                msg, chart_type=spec.chart_type.value,
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
        }
        render_fn = renderers.get(spec.chart_type)
        if render_fn is None:
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
                x_pos + offset, data[col],
                width=width, label=col, color=color,
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
                y_pos + offset, data[col],
                height=bar_height, label=col, color=color,
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
                x_pos, values,
                bottom=bottom, label=col, color=color,
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
                x, data[col], alpha=0.5, label=col, color=color,
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
            values, labels=labels, colors=colors,
            autopct="%1.1f%%", startangle=90,
        )
        ax.set_aspect("equal")

    def _render_donut(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        ax: Axes,
        palette: list[str],
    ) -> None:
        from matplotlib.patches import Circle  # noqa: PLC0415

        labels = data[spec.x_column].tolist()
        values = data[spec.y_columns[0]]
        colors = palette[: len(labels)]
        ax.pie(
            values, labels=labels, colors=colors,
            autopct="%1.1f%%", startangle=90, pctdistance=0.85,
        )
        centre = Circle((0, 0), 0.70, fc="white")
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
                data[spec.x_column], data[col],
                label=col, color=color,
            )

    def _render_heatmap(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        ax: Axes,
        palette: list[str],  # noqa: ARG002
    ) -> None:
        import seaborn as sns  # noqa: PLC0415

        numeric_cols = [
            c for c in spec.y_columns if c in data.columns
        ]
        if not numeric_cols:
            msg = "Heatmap requires numeric y_columns"
            raise ChartError(msg, chart_type="heatmap")
        pivot_data = data.set_index(spec.x_column)[numeric_cols]
        sns.heatmap(
            pivot_data, ax=ax, annot=True, fmt=".1f", cmap="YlOrRd",
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
                data=plot_data, ax=ax,
                palette=palette[: len(spec.y_columns)],
            )

    # -- common styling --------------------------------------------------------

    def _apply_common_styling(
        self,
        spec: ChartSpec,
        theme: ThemeSpec,
        ax: Axes,
    ) -> None:
        """Apply shared styling: title, axis labels, legend."""
        ax.set_title(
            spec.title, fontsize=theme.chart.title_size, pad=12,
        )

        # Pie/donut charts have no x/y labels
        if spec.chart_type not in (ChartType.PIE, ChartType.DONUT):
            ax.set_xlabel(
                spec.x_label or spec.x_column,
                fontsize=theme.chart.label_size,
            )
            if spec.y_label:
                ax.set_ylabel(
                    spec.y_label, fontsize=theme.chart.label_size,
                )
            elif len(spec.y_columns) == 1:
                ax.set_ylabel(
                    spec.y_columns[0],
                    fontsize=theme.chart.label_size,
                )

        _no_legend_types = (
            ChartType.PIE, ChartType.DONUT,
            ChartType.HEATMAP, ChartType.BOX,
        )
        if (
            spec.legend
            and len(spec.y_columns) > 1
            and spec.chart_type not in _no_legend_types
        ):
            ax.legend(loc=spec.legend_position)

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
