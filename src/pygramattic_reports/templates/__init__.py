"""Template engine for pygramattic-reports.

Load, validate, and render report templates.

Usage::

    from pygramattic_reports.templates import TemplateLoader, TemplateRenderer

    loader = TemplateLoader(templates_dir)
    template = loader.load("quarterly_report")

    renderer = TemplateRenderer()
    resolved = renderer.resolve_template(template, context)
"""

from .loader import TemplateLoader
from .renderer import TemplateRenderer

__all__ = ["TemplateLoader", "TemplateRenderer"]
