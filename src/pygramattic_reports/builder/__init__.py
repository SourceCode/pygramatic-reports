"""Report builder for pygramattic-reports.

Assembles reports from templates, themes, and datasets.

Usage::

    from pygramattic_reports.builder import ReportBuilder, load_build_config

    config = load_build_config(Path("report_config.yaml"), app_config, storage)
    builder = ReportBuilder(chart_engine, template_renderer)
    report, build_log = builder.build(config)
"""

from .builder import ReportBuilder
from .config import BuildConfig
from .config_loader import load_build_config

__all__ = ["BuildConfig", "ReportBuilder", "load_build_config"]
