"""Template loader for pygramattic-reports.

Loads and validates report templates from YAML files into
``TemplateSpec`` models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from pydantic import ValidationError

from pygramattic_reports.exceptions import TemplateError
from pygramattic_reports.logging import get_logger
from pygramattic_reports.models import SectionSource, TemplateSpec

if TYPE_CHECKING:
    from pathlib import Path

_logger = get_logger("templates.loader")


class TemplateLoader:
    """Loads and validates report templates from YAML files.

    Templates are stored as YAML files in the templates directory.
    Each file defines one template.

    Usage::

        loader = TemplateLoader(templates_dir=Path("sample_templates"))
        template = loader.load("quarterly_report")
        all_names = loader.list_templates()
    """

    def __init__(self, templates_dir: Path) -> None:  # noqa: D107
        self.templates_dir = templates_dir

    def load(self, template_name: str) -> TemplateSpec:
        """Load a template by name.

        Looks for ``{templates_dir}/{template_name}.yaml``.

        Args:
            template_name: Name of the template (without ``.yaml`` extension).

        Returns:
            Parsed and validated ``TemplateSpec``.

        Raises:
            TemplateError: If the template is not found or invalid.
        """
        path = self.templates_dir / f"{template_name}.yaml"
        if not path.is_file():
            msg = f"Template not found: {path}"
            raise TemplateError(msg, template_name=template_name)

        try:
            with path.open() as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            msg = f"Invalid YAML in template {template_name}: {exc}"
            raise TemplateError(msg, template_name=template_name) from exc

        if not isinstance(data, dict):
            msg = f"Template {template_name} must be a YAML mapping"
            raise TemplateError(msg, template_name=template_name)

        try:
            template = TemplateSpec(**data)
        except ValidationError as exc:
            msg = f"Invalid template {template_name}: {exc}"
            raise TemplateError(msg, template_name=template_name) from exc

        _logger.info(
            "Loaded template",
            name=template_name,
            sections=len(template.sections),
        )
        return template

    def list_templates(self) -> list[str]:
        """List all available template names.

        Returns:
            Sorted list of template names (without ``.yaml`` extension).
        """
        if not self.templates_dir.is_dir():
            return []
        return sorted(
            p.stem for p in self.templates_dir.glob("*.yaml")
        )

    def validate(self, template: TemplateSpec) -> list[str]:
        """Validate a template and return any warnings.

        Checks:
            - Data-sourced sections reference a dataset name.
            - Chart sections have required chart fields.
            - AI sections have a prompt.
            - No duplicate section titles.

        Args:
            template: The template to validate.

        Returns:
            List of warning messages (empty if valid).
        """
        warnings: list[str] = []
        titles_seen: set[str] = set()

        for i, section in enumerate(template.sections):
            prefix = f"Section {i} ({section.type})"

            if section.source == SectionSource.DATA and not section.dataset:
                warnings.append(f"{prefix}: data-sourced section missing 'dataset'")

            if section.source == SectionSource.CHART:
                if not section.chart_type:
                    warnings.append(f"{prefix}: chart section missing 'chart_type'")
                if not section.x_column:
                    warnings.append(f"{prefix}: chart section missing 'x_column'")
                if not section.y_columns:
                    warnings.append(f"{prefix}: chart section missing 'y_columns'")

            if section.source == SectionSource.AI_GENERATED and not section.ai_prompt:
                warnings.append(f"{prefix}: AI section missing 'ai_prompt'")

            if section.title:
                if section.title in titles_seen:
                    warnings.append(f"{prefix}: duplicate title {section.title!r}")
                titles_seen.add(section.title)

        return warnings
