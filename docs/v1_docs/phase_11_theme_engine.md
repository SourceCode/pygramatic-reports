# Phase 11: Theme Engine

## Objective

Build the theme engine that loads YAML theme definitions and provides styling configuration to the chart engine, report builder, and output adapters. Themes control fonts, colors, spacing, and chart aesthetics.

## Why This Phase Is Eleventh

Templates (Phase 10) define what goes in a report; themes define how it looks. The chart engine (Phase 12) and output adapters (Phases 14-15) need theme data to apply consistent styling. Themes must be loadable before those phases.

## Tasks

### Task 11.1: Implement the Theme Loader

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/themes/loader.py`

**Description:** Load and validate theme YAML files into `ThemeSpec` models.

**Interface:**
```python
from pathlib import Path
from pygramattic_reports.models import ThemeSpec


class ThemeLoader:
    """Loads and validates report themes from YAML files.

    Themes control visual styling: fonts, colors, spacing, chart appearance.
    They are swappable and applied independently of templates.

    Usage:
        loader = ThemeLoader(themes_dir=Path("sample_themes"))
        theme = loader.load("corporate_blue")
        all_themes = loader.list_themes()
    """

    def __init__(self, themes_dir: Path):
        self.themes_dir = themes_dir

    def load(self, theme_name: str) -> ThemeSpec:
        """Load a theme by name.

        Looks for {themes_dir}/{theme_name}.yaml

        Raises:
            ThemeError: If theme not found or invalid.
        """
        ...

    def list_themes(self) -> list[str]:
        """List all available theme names."""
        ...
```

---

### Task 11.2: Implement Theme Application Helpers

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/themes/applicator.py`

**Description:** Utilities that translate theme specs into format-specific styling objects.

**Requirements:**
- Convert `ThemeSpec` to matplotlib rcParams dict (for chart rendering)
- Convert `ThemeSpec` to DOCX style configuration (for Word output)
- Convert `ThemeSpec` to CSS-like dict (for Markdown/HTML output)

```python
from pygramattic_reports.models import ThemeSpec


class ThemeApplicator:
    """Translates abstract ThemeSpec into format-specific style objects.

    The ThemeSpec is format-agnostic. The applicator converts it into
    the specific parameters needed by matplotlib, python-docx, etc.
    """

    def __init__(self, theme: ThemeSpec):
        self.theme = theme

    def to_matplotlib_params(self) -> dict:
        """Convert theme to matplotlib rcParams dictionary.

        Used by the Chart Engine to apply consistent styling.

        Returns dict like:
        {
            "figure.facecolor": "#ffffff",
            "axes.facecolor": "#ffffff",
            "axes.edgecolor": "#2c3e50",
            "axes.grid": True,
            "grid.color": "#e0e0e0",
            "grid.alpha": 0.5,
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial"],
            "font.size": 11,
            "axes.titlesize": 14,
            "axes.labelsize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 10,
            "lines.linewidth": 2.0,
        }
        """
        ...

    def to_docx_styles(self) -> dict:
        """Convert theme to python-docx style parameters.

        Returns a dict that the DOCX output adapter uses to configure
        document styles.

        Returns dict like:
        {
            "fonts": {"heading": "Arial", "body": "Calibri"},
            "sizes": {"title": 24, "heading": 16, "body": 11, "caption": 9},
            "colors": {"primary": "#1a5276", "text": "#2c3e50"},
            "spacing": {"section_gap_pt": 18, "paragraph_gap_pt": 6},
        }
        """
        ...

    def to_markdown_styles(self) -> dict:
        """Convert theme to styling hints for Markdown output.

        Markdown is plain text and does not natively support styling.
        These hints are used when embedding HTML in Markdown or for
        downstream processors that support styled Markdown (e.g., pandoc).

        Returns minimal styling hints that can be used in HTML wrappers.
        """
        ...

    def get_chart_palette(self) -> list[str]:
        """Get the ordered color palette for charts."""
        return self.theme.colors.chart_palette

    def get_color(self, name: str) -> str:
        """Get a named color from the theme.

        Args:
            name: Color name ("primary", "secondary", "accent", etc.)

        Returns:
            Hex color string.
        """
        ...
```

---

### Task 11.3: Create Default Theme

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/sample_themes/default.yaml`

```yaml
name: default
description: Clean, professional default theme

fonts:
  heading: Arial
  body: Calibri
  monospace: Courier New
  size_title: 24
  size_heading: 16
  size_body: 11
  size_caption: 9

colors:
  primary: "#2c3e50"
  secondary: "#3498db"
  accent: "#e74c3c"
  background: "#ffffff"
  text: "#2c3e50"
  text_light: "#7f8c8d"
  chart_palette:
    - "#2c3e50"
    - "#3498db"
    - "#2ecc71"
    - "#e74c3c"
    - "#f39c12"
    - "#9b59b6"
    - "#1abc9c"
    - "#e67e22"

spacing:
  section_gap_pt: 18
  paragraph_gap_pt: 6
  page_margin_inches: 1.0

chart:
  background_color: "#ffffff"
  grid: true
  grid_color: "#ecf0f1"
  grid_alpha: 0.7
  title_size: 14
  label_size: 11
  tick_size: 9
  legend_size: 10
  line_width: 2.0
```

---

### Task 11.4: Create Corporate Blue Theme

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/sample_themes/corporate_blue.yaml`

```yaml
name: corporate_blue
description: Professional corporate theme with blue tones

fonts:
  heading: Arial
  body: Calibri
  monospace: Consolas
  size_title: 28
  size_heading: 18
  size_body: 11
  size_caption: 9

colors:
  primary: "#1a5276"
  secondary: "#2e86c1"
  accent: "#d4ac0d"
  background: "#ffffff"
  text: "#1c2833"
  text_light: "#566573"
  chart_palette:
    - "#1a5276"
    - "#2e86c1"
    - "#85c1e9"
    - "#d4ac0d"
    - "#1e8449"
    - "#a93226"
    - "#7d3c98"
    - "#f39c12"

spacing:
  section_gap_pt: 24
  paragraph_gap_pt: 8
  page_margin_inches: 1.0

chart:
  background_color: "#fafafa"
  grid: true
  grid_color: "#d5dbdb"
  grid_alpha: 0.5
  title_size: 16
  label_size: 12
  tick_size: 10
  legend_size: 11
  line_width: 2.5
```

---

### Task 11.5: Create Themes Package Init

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/themes/__init__.py`

```python
"""Theme engine for pygramattic-reports.

Load themes and translate them to format-specific styling.

Usage:
    from pygramattic_reports.themes import ThemeLoader, ThemeApplicator

    loader = ThemeLoader(themes_dir)
    theme = loader.load("corporate_blue")
    applicator = ThemeApplicator(theme)
    mpl_params = applicator.to_matplotlib_params()
"""
from .loader import ThemeLoader
from .applicator import ThemeApplicator

__all__ = ["ThemeLoader", "ThemeApplicator"]
```

---

### Task 11.6: Write Theme Tests

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_themes.py`

**Test cases:**
1. `test_load_theme` -- Load a valid YAML theme
2. `test_load_theme_not_found` -- Raises `ThemeError`
3. `test_load_theme_defaults` -- Missing optional fields use defaults
4. `test_list_themes` -- Lists all themes in directory
5. `test_to_matplotlib_params` -- Produces valid rcParams dict
6. `test_to_docx_styles` -- Produces correct DOCX style config
7. `test_get_chart_palette` -- Returns correct color list
8. `test_get_color` -- Returns correct named color
9. `test_theme_swapping` -- Two different themes produce different params

---

## Dependencies

- **Depends on:** Phase 02 (ThemeSpec model), Phase 04 (ThemeError)
- **Blocks:** Phase 12 (chart engine uses themes), Phase 13 (builder uses themes), Phase 14-15 (output adapters use themes)

## Acceptance Criteria

1. `ThemeLoader` loads and validates YAML themes
2. `ThemeApplicator` converts themes to matplotlib params, DOCX styles, etc.
3. Default and corporate_blue themes exist and validate
4. Themes are fully swappable (changing theme changes styling, not structure)
5. All tests pass

## References

- PRD Templates & Themes: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 96-104)
- PRD Chart Engine Themes: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 318-325)
