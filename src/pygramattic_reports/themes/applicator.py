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

    def to_css_variables(self) -> str:
        """Generate CSS custom properties (variables) from the theme.

        Returns:
            String of CSS variable definitions (e.g. --color-primary: #123;).
        """
        c = self.theme.colors
        f = self.theme.fonts
        s = self.theme.spacing
        ch = self.theme.chart

        # Generate Palette Variables
        palette_vars = []
        for i, color in enumerate(c.chart_palette):
            palette_vars.append(f"--chart-color-{i}: {color};")

        vars_list = [
            # Colors
            f"--color-primary: {c.primary};",
            f"--color-secondary: {c.secondary};",
            f"--color-accent: {c.accent};",
            f"--color-background: {c.background};",
            f"--color-text: {c.text};",
            f"--color-text-light: {c.text_light};",
            # Fonts
            f"--font-heading: {f.heading}, sans-serif;",
            f"--font-body: {f.body}, sans-serif;",
            f"--font-monospace: {f.monospace}, monospace;",
            # Sizes
            f"--size-title: {f.size_title}pt;",
            f"--size-heading: {f.size_heading}pt;",
            f"--size-body: {f.size_body}pt;",
            f"--size-caption: {f.size_caption}pt;",
            # Spacing
            f"--spacing-section: {s.section_gap_pt}pt;",
            f"--spacing-paragraph: {s.paragraph_gap_pt}pt;",
            f"--page-margin: {s.page_margin_inches}in;",
            # Chart
            f"--chart-bg: {ch.background_color};",
            f"--chart-grid: {ch.grid_color};",
        ] + palette_vars

        return "\n    ".join(vars_list)

    def to_css_styles(self) -> str:
        """Generate global CSS styles and utility classes.

        Returns:
            String of CSS rules.
        """
        # We can implement a simple baseline CSS here using the variables
        return """
            :root {
                /* System Variables */
                %s
            }

            body {
                font-family: var(--font-body);
                color: var(--color-text);
                background-color: var(--color-background);
                line-height: 1.6;
                margin: 0;
                padding: var(--page-margin);
            }

            h1, h2, h3, h4, h5, h6 {
                font-family: var(--font-heading);
                color: var(--color-primary);
                margin-top: var(--spacing-section);
                margin-bottom: var(--spacing-paragraph);
            }
            
            h1 { font-size: var(--size-title); border-bottom: 2px solid var(--color-secondary); padding-bottom: 0.5rem; }
            h2 { font-size: var(--size-heading); border-bottom: 1px solid #eee; }
            h3 { font-size: calc(var(--size-heading) * 0.85); color: var(--color-secondary); }
            
            p {
                margin-bottom: var(--spacing-paragraph);
                font-size: var(--size-body);
            }
            
            code, pre {
                font-family: var(--font-monospace);
                background-color: #f5f5f5;
                border-radius: 4px;
            }
            
            pre { padding: 1rem; overflow-x: auto; font-size: 0.9em; border: 1px solid #ddd; }

            /* --- Layout Components --- */

            /* Metric Cards */
            .metric-card-container {
                display: flex;
                flex-wrap: wrap;
                gap: 1rem;
                margin-bottom: var(--spacing-section);
            }
            
            .metric-card {
                border: 1px solid #eee;
                border-left: 4px solid var(--color-secondary);
                border-radius: 4px;
                padding: 1rem;
                min-width: 150px;
                flex: 1;
                background:white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            
            .metric-label {
                font-size: 0.8em;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: var(--color-text-light);
            }
            
            .metric-value {
                font-size: 1.8em;
                font-weight: bold;
                color: var(--color-primary);
                margin: 0.25rem 0;
            }

            /* Callouts */
            .callout {
                padding: 1rem;
                margin-bottom: 1rem;
                border-left: 4px solid #ccc;
                border-radius: 0 4px 4px 0;
                background-color: #f9f9f9;
            }
            
            .callout-title {
                font-weight: bold;
                margin-bottom: 0.5rem;
                display:block;
            }
            
            .callout-info { border-left-color: #3498db; background-color: #ebf5fb; }
            .callout-warning { border-left-color: #f39c12; background-color: #fef9e7; }
            .callout-success { border-left-color: #2ecc71; background-color: #eafaf1; }
            .callout-danger { border-left-color: #e74c3c; background-color: #fdedec; }

            /* Lists */
            ul.styled-list {
                list-style-type: disc;
                padding-left: 1.5rem;
            }
            
            /* Quotes */
            blockquote {
                border-left: 3px solid var(--color-accent);
                margin: 1.5rem 0;
                padding: 0.5rem 1.5rem;
                font-style: italic;
                background: #fdfdfd;
                color: #555;
            }
            
            .quote-author {
                display: block;
                margin-top: 0.5rem;
                font-style: normal;
                font-weight: bold;
                font-size: 0.9em;
                color: var(--color-text-light);
            }
            
            /* Columns */
            .columns-container {
                display: grid;
                gap: 2rem;
                margin-bottom: var(--spacing-section);
            }
            
            @media (min-width: 768px) {
                .columns-container {
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                }
            }

            /* Tables */
            table { width: 100%%; border-collapse: collapse; margin-bottom: 1.5rem; }
            th { text-align: left; background: #f8f9fa; border-bottom: 2px solid #dee2e6; padding: 0.75rem; color: var(--color-text-light); font-size: 0.9em; text-transform:uppercase; }
            td { border-bottom: 1px solid #dee2e6; padding: 0.75rem; vertical-align:top; }
            tr:nth-child(even) { background-color: #f8f9fa; }

            /* Print Overrides */
            @media print {
                body { padding: 0; font-size: 11pt; }
                .page-break { page-break-before: always; }
                a { text-decoration: none; color: black; }
            }
        """ % self.to_css_variables()
