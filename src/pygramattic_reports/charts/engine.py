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
        self,
        name: str,
        renderer: BaseChartRenderer,
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

        # We cache the result of the renderer, not the whole generate method
        # because _extract_data might be fast enough, but render is slow.
        # However, to use the decorator, we apply it to a method.
        # Let's use the property of get_cache()
        from pygramattic_reports.core.cache import get_cache

        # We manually check cache or use a helper
        # Since 'data' is a dataframe, we need to be careful with key generation
        # Let's assume we want to cache based on spec + dataset.id + theme
        cache = get_cache()
        key = cache.generate_key(spec.model_dump_json(), dataset.id, theme.model_dump_json())
        cached = cache.get(key)
        if cached:
            _logger.debug("Chart cache hit", key=key)
            return bytes(cached)

        result = renderer.render(spec, data, theme)
        cache.put(key, result)
        return result

    def generate_batch(
        self,
        specs: list[tuple[ChartSpec, Dataset, ThemeSpec]],
        max_workers: int | None = None,
    ) -> list[bytes]:
        """Generate multiple charts in parallel.

        Args:
            specs: List of (spec, dataset, theme) tuples.
            max_workers: Number of parallel workers.

        Returns:
            List of image bytes in same order.
        """
        import concurrent.futures

        results = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            # We map to a standalone function to avoid pickling self
            # We need to pass the renderer name, not the instance
            futures = [
                executor.submit(_render_task, s[0].renderer.value, s[0], s[1], s[2]) for s in specs
            ]

            # Wait for all
            results = [f.result() for f in futures]

        return results

    @staticmethod
    def _extract_data(
        spec: ChartSpec,
        dataset: Dataset,
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

        missing = [c for c in required_cols if c not in dataset.dataframe.columns]
        if missing:
            msg = f"Columns not found in dataset '{dataset.name}': {missing}"
            raise ChartError(
                msg,
                chart_type=spec.chart_type.value,
            )

        data = dataset.dataframe[required_cols].copy()

        if spec.sort_by and spec.sort_by in data.columns:
            data = data.sort_values(spec.sort_by)

        if spec.limit:
            data = data.head(spec.limit)

        return data


def _render_task(
    renderer_name: str,
    spec: ChartSpec,
    dataset: Dataset,
    theme: ThemeSpec,
) -> bytes:
    """Standalone task for parallel execution."""
    # We must instantiate renderer here or pass it.
    # Renderers are lightweight, so instantiating is fine.
    # But we need the registry. For now, hardcode known renderers or allow passing class.
    from .matplotlib_renderer import MatplotlibRenderer

    if renderer_name == "matplotlib":
        renderer = MatplotlibRenderer()
    else:
        # Fallback or error
        # In a real system, we'd have a better registry or pass the renderer class
        msg = f"Renderer not supported in parallel mode: {renderer_name}"
        raise ChartError(msg)

    return renderer.render(spec, ChartEngine._extract_data(spec, dataset), theme)
