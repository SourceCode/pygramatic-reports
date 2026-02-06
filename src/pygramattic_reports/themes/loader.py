"""Theme loader for pygramattic-reports.

Loads and validates report themes from YAML files into
``ThemeSpec`` models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from pydantic import ValidationError

from pygramattic_reports.exceptions import ThemeError
from pygramattic_reports.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

    from pygramattic_reports.models import ThemeSpec

_logger = get_logger("themes.loader")


class ThemeLoader:
    """Loads and validates report themes from YAML files.

    Themes control visual styling: fonts, colors, spacing, chart appearance.
    They are swappable and applied independently of templates.

    Usage::

        loader = ThemeLoader(themes_dir=Path("sample_themes"))
        theme = loader.load("corporate_blue")
        all_themes = loader.list_themes()
    """

    def __init__(self, themes_dir: Path) -> None:  # noqa: D107
        self.themes_dir = themes_dir

    def load(self, theme_name: str) -> ThemeSpec:
        """Load a theme by name.

        Looks for ``{themes_dir}/{theme_name}.yaml``.

        Args:
            theme_name: Name of the theme (without ``.yaml`` extension).

        Returns:
            Parsed and validated ``ThemeSpec``.

        Raises:
            ThemeError: If the theme is not found or invalid.
        """
        from pygramattic_reports.models import ThemeSpec as _ThemeSpec  # noqa: PLC0415

        path = self.themes_dir / f"{theme_name}.yaml"
        if not path.is_file():
            msg = f"Theme not found: {path}"
            raise ThemeError(msg)

        try:
            with path.open() as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            msg = f"Invalid YAML in theme {theme_name}: {exc}"
            raise ThemeError(msg) from exc

        if not isinstance(data, dict):
            msg = f"Theme {theme_name} must be a YAML mapping"
            raise ThemeError(msg)

        try:
            theme = _ThemeSpec(**data)
        except ValidationError as exc:
            msg = f"Invalid theme {theme_name}: {exc}"
            raise ThemeError(msg) from exc

        _logger.info("Loaded theme", name=theme_name)
        return theme

    def list_themes(self) -> list[str]:
        """List all available theme names.

        Returns:
            Sorted list of theme names (without ``.yaml`` extension).
        """
        if not self.themes_dir.is_dir():
            return []
        return sorted(p.stem for p in self.themes_dir.glob("*.yaml"))
