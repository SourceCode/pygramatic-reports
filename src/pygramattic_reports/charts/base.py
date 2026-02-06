"""Abstract base class for chart renderers.

Decouples chart specification from rendering library, allowing
multiple backends (matplotlib, plotly) behind a common interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from pygramattic_reports.models import ChartSpec, ThemeSpec


class BaseChartRenderer(ABC):
    """Abstract chart renderer.

    Takes a ChartSpec (what to draw), a DataFrame (the data),
    and a ThemeSpec (how it should look), and produces image bytes.

    Implementations exist for matplotlib (and potentially plotly).
    """

    @abstractmethod
    def render(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        theme: ThemeSpec,
    ) -> bytes:
        """Render a chart to image bytes.

        Args:
            spec: What chart to render (type, columns, title, etc.).
            data: The data to visualize.
            theme: Visual styling to apply.

        Returns:
            Image bytes in the format specified by ``spec.output_format``.

        Raises:
            ChartError: If rendering fails.
        """

    @abstractmethod
    def supported_chart_types(self) -> list[str]:
        """List chart types this renderer supports.

        Returns:
            List of chart type value strings.
        """
