"""Build configuration model for pygramattic-reports.

Defines the typed configuration for a report build,
specifying template, theme, datasets, and output preferences.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class BuildConfig(BaseModel):
    """Configuration for a single report build.

    Loaded from a ``report_config.yaml`` file or constructed
    programmatically.

    Attributes:
        report_name: Name of the generated report.
        template: Resolved template specification.
        theme: Resolved theme specification.
        datasets: Name-to-Dataset mapping.
        primary_dataset: Name of the main dataset.
        output_formats: Desired output formats.
        output_directory: Where to write output files.
        ai_enabled: Whether AI content generation is enabled.
        ai_sections: Section types that should use AI.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    report_name: str
    template: Any  # TemplateSpec — uses Any for Dataset compat
    theme: Any  # ThemeSpec — uses Any for Dataset compat
    datasets: dict[str, Any]  # name -> Dataset
    primary_dataset: str | None = None

    output_formats: list[str] = ["md"]
    output_directory: str = "data/reports/"

    ai_enabled: bool = False
    ai_sections: list[str] = []
