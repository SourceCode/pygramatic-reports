"""Chart and graph generation engine.

Supports matplotlib/seaborn rendering with theme-aware styling.

Usage::

    from pygramattic_reports.charts import ChartEngine

    engine = ChartEngine()
    image_bytes = engine.generate(chart_spec, dataset, theme)
"""

from .engine import ChartEngine
from .matplotlib_renderer import MatplotlibRenderer

__all__ = ["ChartEngine", "MatplotlibRenderer"]
