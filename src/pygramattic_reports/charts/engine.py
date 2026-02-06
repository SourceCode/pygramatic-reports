"""Chart generation engine for pygramattic-reports.

High-level orchestrator that routes chart specs to the appropriate
renderer and manages data extraction from datasets.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygramattic_reports.exceptions import ChartError
from pygramattic_reports.logging import get_logger

from .matplotlib_renderer import MatplotlibRenderer

if TYPE_CHECKING:
    import pandas as pd

    from pygramattic_reports.models import ChartSpec, Dataset, ThemeSpec

    from .base import BaseChartRenderer

_logger = get_logger("charts.engine")


class ChartEngine:
    """High-level chart generation engine.

    Routes ChartSpec to the appropriate renderer, handles data extraction
    from Datasets, and manages the rendering pipeline.

    Usage::

        engine = ChartEngine()
        chart_bytes = engine.generate(spec, dataset, theme)
    """

    def __init__(self) -> None:  # noqa: D107
        self._renderers: dict[str, BaseChartRenderer] = {
            "matplotlib": MatplotlibRenderer(),
        }

    def register_renderer(
        self, name: str, renderer: BaseChartRenderer,
    ) -> None:
        """Register an additional renderer (e.g., plotly).

        Args:
            name: Renderer name matching ``ChartRenderer`` enum values.
            renderer: Renderer instance.
        """
        self._renderers[name] = renderer

    def generate(
        self,
        spec: ChartSpec,
        dataset: Dataset,
        theme: ThemeSpec,
    ) -> bytes:
        """Generate a chart from a spec and dataset.

        Args:
            spec: Chart specification.
            dataset: Source data.
            theme: Visual styling.

        Returns:
            Image bytes.

        Raises:
            ChartError: If rendering fails.
        """
        renderer = self._renderers.get(spec.renderer.value)
        if renderer is None:
            msg = f"Renderer not available: {spec.renderer.value}"
            raise ChartError(msg)

        data = self._extract_data(spec, dataset)

        _logger.info(
            "Generating chart",
            chart_type=spec.chart_type.value,
            dataset=dataset.name,
            rows=len(data),
        )

        return renderer.render(spec, data, theme)

    @staticmethod
    def _extract_data(
        spec: ChartSpec, dataset: Dataset,
    ) -> pd.DataFrame:
        """Extract the columns needed for the chart from the dataset.

        Validates that required columns exist. Applies optional
        sorting and limiting.

        Args:
            spec: Chart specification with column requirements.
            dataset: Source dataset.

        Returns:
            DataFrame with only the required columns.

        Raises:
            ChartError: If required columns are missing.
        """
        required_cols = [spec.x_column, *spec.y_columns]
        if spec.group_by:
            required_cols.append(spec.group_by)

        missing = [
            c for c in required_cols
            if c not in dataset.dataframe.columns
        ]
        if missing:
            msg = (
                f"Columns not found in dataset "
                f"'{dataset.name}': {missing}"
            )
            raise ChartError(
                msg, chart_type=spec.chart_type.value,
            )

        data = dataset.dataframe[required_cols].copy()

        if spec.sort_by and spec.sort_by in data.columns:
            data = data.sort_values(spec.sort_by)

        if spec.limit:
            data = data.head(spec.limit)

        return data
