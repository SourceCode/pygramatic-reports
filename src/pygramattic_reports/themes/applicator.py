"""Theme application helpers for pygramattic-reports.

Translates abstract ``ThemeSpec`` into format-specific style objects
for matplotlib, python-docx, and Markdown/HTML output.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pygramattic_reports.models import ThemeSpec


class ThemeApplicator:
    """Translates abstract ThemeSpec into format-specific style objects.

    The ThemeSpec is format-agnostic. The applicator converts it into
    the specific parameters needed by matplotlib, python-docx, etc.

    Usage::

        applicator = ThemeApplicator(theme)
        mpl_params = applicator.to_matplotlib_params()
        docx_styles = applicator.to_docx_styles()
    """

    def __init__(self, theme: ThemeSpec) -> None:  # noqa: D107
        self.theme = theme

    def to_matplotlib_params(self) -> dict[str, Any]:
        """Convert theme to matplotlib rcParams dictionary.

        Used by the Chart Engine to apply consistent styling.

        Returns:
            Dictionary of matplotlib rcParams.
        """
        chart = self.theme.chart
        fonts = self.theme.fonts
        colors = self.theme.colors

        return {
            "figure.facecolor": chart.background_color,
            "axes.facecolor": chart.background_color,
            "axes.edgecolor": colors.text,
            "axes.grid": chart.grid,
            "grid.color": chart.grid_color,
            "grid.alpha": chart.grid_alpha,
            "font.family": "sans-serif",
            "font.sans-serif": [fonts.heading],
            "font.size": fonts.size_body,
            "axes.titlesize": chart.title_size,
            "axes.labelsize": chart.label_size,
            "xtick.labelsize": chart.tick_size,
            "ytick.labelsize": chart.tick_size,
            "legend.fontsize": chart.legend_size,
            "lines.linewidth": chart.line_width,
        }

    def to_docx_styles(self) -> dict[str, Any]:
        """Convert theme to python-docx style parameters.

        Returns a dict that the DOCX output adapter uses to configure
        document styles.

        Returns:
            Dictionary with fonts, sizes, colors, and spacing config.
        """
        fonts = self.theme.fonts
        colors = self.theme.colors
        spacing = self.theme.spacing

        return {
            "fonts": {
                "heading": fonts.heading,
                "body": fonts.body,
                "monospace": fonts.monospace,
            },
            "sizes": {
                "title": fonts.size_title,
                "heading": fonts.size_heading,
                "body": fonts.size_body,
                "caption": fonts.size_caption,
            },
            "colors": {
                "primary": colors.primary,
                "secondary": colors.secondary,
                "accent": colors.accent,
                "text": colors.text,
                "text_light": colors.text_light,
                "background": colors.background,
            },
            "spacing": {
                "section_gap_pt": spacing.section_gap_pt,
                "paragraph_gap_pt": spacing.paragraph_gap_pt,
                "page_margin_inches": spacing.page_margin_inches,
            },
        }

    def to_markdown_styles(self) -> dict[str, Any]:
        """Convert theme to styling hints for Markdown output.

        Markdown is plain text and does not natively support styling.
        These hints are used when embedding HTML in Markdown or for
        downstream processors that support styled Markdown (e.g., pandoc).

        Returns:
            Dictionary with CSS-like styling hints.
        """
        fonts = self.theme.fonts
        colors = self.theme.colors

        return {
            "body_font": fonts.body,
            "heading_font": fonts.heading,
            "code_font": fonts.monospace,
            "text_color": colors.text,
            "heading_color": colors.primary,
            "link_color": colors.secondary,
            "accent_color": colors.accent,
            "background_color": colors.background,
        }

    def get_chart_palette(self) -> list[str]:
        """Get the ordered color palette for charts.

        Returns:
            List of hex color strings.
        """
        return list(self.theme.colors.chart_palette)

    def get_color(self, name: str) -> str:
        """Get a named color from the theme.

        Args:
            name: Color name (``"primary"``, ``"secondary"``, ``"accent"``,
                ``"background"``, ``"text"``, ``"text_light"``).

        Returns:
            Hex color string.

        Raises:
            ValueError: If color name is not recognized.
        """
        colors = self.theme.colors
        color_map: dict[str, str] = {
            "primary": colors.primary,
            "secondary": colors.secondary,
            "accent": colors.accent,
            "background": colors.background,
            "text": colors.text,
            "text_light": colors.text_light,
        }
        if name not in color_map:
            msg = f"Unknown color name {name!r}, expected one of {sorted(color_map)}"
            raise ValueError(msg)
        return color_map[name]
