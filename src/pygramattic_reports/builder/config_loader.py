"""Report config loader for pygramattic-reports.

Loads a ``report_config.yaml`` file and resolves all references
(template, theme, datasets) into a ``BuildConfig``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from pygramattic_reports.exceptions import BuildError
from pygramattic_reports.logging import get_logger
from pygramattic_reports.templates import TemplateLoader
from pygramattic_reports.themes import ThemeLoader

from .config import BuildConfig

if TYPE_CHECKING:
    from pathlib import Path

    from pygramattic_reports.config import AppConfig
    from pygramattic_reports.storage import StorageManager

_logger = get_logger("builder.config_loader")


def load_build_config(
    config_path: Path,
    app_config: AppConfig,
    storage: StorageManager,
) -> BuildConfig:
    """Load a report_config.yaml and resolve all references.

    Resolves:
        - Template name to ``TemplateSpec`` (from templates_dir)
        - Theme name to ``ThemeSpec`` (from themes_dir)
        - Dataset names to ``Dataset`` objects (from storage)

    Args:
        config_path: Path to ``report_config.yaml``.
        app_config: Application configuration.
        storage: Storage manager for loading datasets.

    Returns:
        Fully resolved ``BuildConfig``.

    Raises:
        BuildError: If config is invalid or references cannot be resolved.
    """
    try:
        with config_path.open() as f:
            data = yaml.safe_load(f)
    except Exception as exc:
        msg = f"Failed to load report config: {exc}"
        raise BuildError(msg) from exc

    if not isinstance(data, dict):
        msg = "Report config must be a YAML mapping"
        raise BuildError(msg)

    report_name = data.get("report_name", "Untitled Report")

    template_name = data.get("template", "default")
    template_loader = TemplateLoader(
        templates_dir=app_config.templates_dir,
    )
    try:
        template = template_loader.load(template_name)
    except Exception as exc:
        msg = f"Failed to load template '{template_name}': {exc}"
        raise BuildError(msg) from exc

    theme_name = data.get("theme", "default")
    theme_loader = ThemeLoader(themes_dir=app_config.themes_dir)
    try:
        theme = theme_loader.load(theme_name)
    except Exception as exc:
        msg = f"Failed to load theme '{theme_name}': {exc}"
        raise BuildError(msg) from exc

    dataset_refs = data.get("datasets", {})
    datasets = {}
    for ds_name, ds_id in dataset_refs.items():
        try:
            datasets[ds_name] = storage.load_dataset(ds_id)
        except Exception as exc:
            msg = f"Failed to load dataset '{ds_name}' (id={ds_id}): {exc}"
            raise BuildError(msg) from exc

    _logger.info(
        "Loaded build config",
        report_name=report_name,
        template=template_name,
        theme=theme_name,
        datasets=len(datasets),
    )

    return BuildConfig(
        report_name=report_name,
        template=template,
        theme=theme,
        datasets=datasets,
        primary_dataset=data.get("primary_dataset"),
        output_formats=data.get("output_formats", ["md"]),
        output_directory=data.get("output_directory", "data/reports/"),
        ai_enabled=data.get("ai_enabled", False),
    )
