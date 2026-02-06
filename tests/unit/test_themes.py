"""Tests for the theme engine (Phase 11)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from pygramattic_reports.exceptions import ThemeError
from pygramattic_reports.themes import ThemeApplicator, ThemeLoader

if TYPE_CHECKING:
    from pygramattic_reports.models import ThemeSpec

# ---------- Helpers ----------------------------------------------------------

_SAMPLE_THEMES = Path(__file__).resolve().parent.parent.parent / "sample_themes"


# ---------- Theme Loader tests -----------------------------------------------


class TestLoadTheme:
    """Test loading a valid YAML theme."""

    def test_load_theme(self, tmp_path: Path) -> None:
        """Load a well-formed theme YAML file."""
        yaml_content = """\
name: test_theme
description: A test theme
fonts:
  heading: Helvetica
  body: Georgia
colors:
  primary: "#111111"
  secondary: "#222222"
"""
        (tmp_path / "test_theme.yaml").write_text(yaml_content)
        loader = ThemeLoader(themes_dir=tmp_path)
        theme = loader.load("test_theme")

        assert theme.name == "test_theme"
        assert theme.fonts.heading == "Helvetica"
        assert theme.fonts.body == "Georgia"
        assert theme.colors.primary == "#111111"


class TestLoadThemeNotFound:
    """Test loading a nonexistent theme."""

    def test_load_theme_not_found(self, tmp_path: Path) -> None:
        """Raises ThemeError when theme file missing."""
        loader = ThemeLoader(themes_dir=tmp_path)
        with pytest.raises(ThemeError, match="not found"):
            loader.load("nonexistent")


class TestLoadThemeDefaults:
    """Test that missing optional fields use defaults."""

    def test_load_theme_defaults(self, tmp_path: Path) -> None:
        """Minimal theme YAML uses model defaults."""
        yaml_content = "name: minimal\n"
        (tmp_path / "minimal.yaml").write_text(yaml_content)
        loader = ThemeLoader(themes_dir=tmp_path)
        theme = loader.load("minimal")

        assert theme.name == "minimal"
        # All sub-models should have their defaults
        assert theme.fonts.heading == "Arial"
        assert theme.fonts.size_body == 11
        assert theme.colors.background == "#ffffff"
        assert theme.spacing.section_gap_pt == 18
        assert theme.chart.grid is True


class TestListThemes:
    """Test listing available themes."""

    def test_list_themes(self, tmp_path: Path) -> None:
        """Lists all YAML theme names sorted."""
        (tmp_path / "dark.yaml").write_text("name: dark\n")
        (tmp_path / "bright.yaml").write_text("name: bright\n")
        (tmp_path / "readme.txt").write_text("not a theme")

        loader = ThemeLoader(themes_dir=tmp_path)
        names = loader.list_themes()

        assert names == ["bright", "dark"]

    def test_list_themes_missing_dir(self) -> None:
        """Returns empty list when directory does not exist."""
        loader = ThemeLoader(themes_dir=Path("/nonexistent"))
        assert loader.list_themes() == []


# ---------- Theme Applicator tests -------------------------------------------


def _default_theme() -> ThemeSpec:
    """Load the default theme from sample_themes for testing."""
    loader = ThemeLoader(themes_dir=_SAMPLE_THEMES)
    return loader.load("default")


def _corporate_theme() -> ThemeSpec:
    """Load the corporate_blue theme from sample_themes for testing."""
    loader = ThemeLoader(themes_dir=_SAMPLE_THEMES)
    return loader.load("corporate_blue")


class TestToMatplotlibParams:
    """Test matplotlib rcParams conversion."""

    def test_to_matplotlib_params(self) -> None:
        """Produces valid rcParams dict with expected keys."""
        theme = _default_theme()
        applicator = ThemeApplicator(theme)
        params = applicator.to_matplotlib_params()

        assert params["figure.facecolor"] == "#ffffff"
        assert params["axes.grid"] is True
        assert params["grid.color"] == "#ecf0f1"
        assert params["grid.alpha"] == 0.7
        assert params["font.family"] == "sans-serif"
        assert params["font.sans-serif"] == ["Arial"]
        assert params["font.size"] == 11
        assert params["axes.titlesize"] == 14
        assert params["axes.labelsize"] == 11
        assert params["xtick.labelsize"] == 9
        assert params["ytick.labelsize"] == 9
        assert params["legend.fontsize"] == 10
        assert params["lines.linewidth"] == 2.0


class TestToDocxStyles:
    """Test DOCX style configuration conversion."""

    def test_to_docx_styles(self) -> None:
        """Produces correct DOCX style config."""
        theme = _default_theme()
        applicator = ThemeApplicator(theme)
        styles = applicator.to_docx_styles()

        assert styles["fonts"]["heading"] == "Arial"
        assert styles["fonts"]["body"] == "Calibri"
        assert styles["fonts"]["monospace"] == "Courier New"
        assert styles["sizes"]["title"] == 24
        assert styles["sizes"]["heading"] == 16
        assert styles["sizes"]["body"] == 11
        assert styles["sizes"]["caption"] == 9
        assert styles["colors"]["primary"] == "#2c3e50"
        assert styles["colors"]["text"] == "#2c3e50"
        assert styles["spacing"]["section_gap_pt"] == 18
        assert styles["spacing"]["paragraph_gap_pt"] == 6
        assert styles["spacing"]["page_margin_inches"] == 1.0


class TestGetChartPalette:
    """Test chart palette retrieval."""

    def test_get_chart_palette(self) -> None:
        """Returns correct color list."""
        theme = _default_theme()
        applicator = ThemeApplicator(theme)
        palette = applicator.get_chart_palette()

        assert isinstance(palette, list)
        assert len(palette) == 8
        assert palette[0] == "#2c3e50"
        assert palette[1] == "#3498db"


class TestGetColor:
    """Test named color retrieval."""

    def test_get_color(self) -> None:
        """Returns correct hex color for named colors."""
        theme = _default_theme()
        applicator = ThemeApplicator(theme)

        assert applicator.get_color("primary") == "#2c3e50"
        assert applicator.get_color("secondary") == "#3498db"
        assert applicator.get_color("accent") == "#e74c3c"
        assert applicator.get_color("text") == "#2c3e50"

    def test_get_color_unknown(self) -> None:
        """Raises ValueError for unknown color name."""
        theme = _default_theme()
        applicator = ThemeApplicator(theme)

        with pytest.raises(ValueError, match="Unknown color name"):
            applicator.get_color("neon_pink")


class TestThemeSwapping:
    """Test that different themes produce different params."""

    def test_theme_swapping(self) -> None:
        """Two different themes produce different matplotlib params."""
        default = ThemeApplicator(_default_theme())
        corporate = ThemeApplicator(_corporate_theme())

        default_params = default.to_matplotlib_params()
        corporate_params = corporate.to_matplotlib_params()

        # Corporate has larger title and line_width
        assert corporate_params["axes.titlesize"] == 16
        assert default_params["axes.titlesize"] == 14
        assert corporate_params["lines.linewidth"] == 2.5
        assert default_params["lines.linewidth"] == 2.0

        # Different background colors
        assert corporate_params["figure.facecolor"] == "#fafafa"
        assert default_params["figure.facecolor"] == "#ffffff"

    def test_theme_swapping_docx(self) -> None:
        """Two different themes produce different DOCX styles."""
        default = ThemeApplicator(_default_theme())
        corporate = ThemeApplicator(_corporate_theme())

        default_styles = default.to_docx_styles()
        corporate_styles = corporate.to_docx_styles()

        assert default_styles["sizes"]["title"] == 24
        assert corporate_styles["sizes"]["title"] == 28
        assert default_styles["colors"]["primary"] == "#2c3e50"
        assert corporate_styles["colors"]["primary"] == "#1a5276"


class TestToMarkdownStyles:
    """Test Markdown style hints conversion."""

    def test_to_markdown_styles(self) -> None:
        """Produces CSS-like styling hints."""
        theme = _default_theme()
        applicator = ThemeApplicator(theme)
        styles = applicator.to_markdown_styles()

        assert styles["body_font"] == "Calibri"
        assert styles["heading_font"] == "Arial"
        assert styles["code_font"] == "Courier New"
        assert styles["text_color"] == "#2c3e50"
        assert styles["heading_color"] == "#2c3e50"
        assert styles["link_color"] == "#3498db"


class TestSampleThemesLoadable:
    """Test that the bundled sample themes can be loaded."""

    @pytest.mark.skipif(
        not _SAMPLE_THEMES.is_dir(),
        reason="sample_themes directory not found",
    )
    def test_default_theme_loads(self) -> None:
        """default.yaml loads and validates."""
        loader = ThemeLoader(themes_dir=_SAMPLE_THEMES)
        theme = loader.load("default")
        assert theme.name == "default"

    @pytest.mark.skipif(
        not _SAMPLE_THEMES.is_dir(),
        reason="sample_themes directory not found",
    )
    def test_corporate_blue_theme_loads(self) -> None:
        """corporate_blue.yaml loads and validates."""
        loader = ThemeLoader(themes_dir=_SAMPLE_THEMES)
        theme = loader.load("corporate_blue")
        assert theme.name == "corporate_blue"
