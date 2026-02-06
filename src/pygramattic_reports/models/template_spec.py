"""Template and theme specification models for pygramattic-reports.

Defines the typed models for template and theme YAML files.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict

# --- Template Models ---


class SectionSource(StrEnum):
    """Where section content comes from."""

    STATIC = "static"
    DATA = "data"
    AI_GENERATED = "ai_generated"
    CHART = "chart"


class TemplateSectionSpec(BaseModel):
    """Specification for a single section in a template.

    Attributes:
        type: Section type string.
        source: Where the content comes from.
        content: Static content or Jinja2 template string.
        dataset: Dataset name reference for data-driven sections.
        columns: Which columns to include.
        chart_type: Chart type for chart sections.
        x_column: X-axis column for chart sections.
        y_columns: Y-axis columns for chart sections.
        ai_prompt: Prompt for AI-generated sections.
        ai_max_words: Max words for AI-generated content.
        ai_context: Additional context for the AI.
        title: Section heading.
        level: Heading level.
        condition: Jinja2 condition for conditional rendering.
        page_break_before: Force page break before section.
        page_break_after: Force page break after section.
        orientation: Page orientation for section (portrait/landscape).
    """

    model_config = ConfigDict(frozen=True)

    type: str
    source: SectionSource = SectionSource.STATIC
    content: str | None = None

    # For data-driven sections
    dataset: str | None = None
    columns: list[str] | None = None

    # For chart sections
    chart_type: str | None = None
    x_column: str | None = None
    y_columns: list[str] | None = None

    # For AI-generated sections
    ai_prompt: str | None = None
    ai_max_words: int | None = None
    ai_context: str | None = None

    # Structural
    title: str | None = None
    level: int = 2
    condition: str | None = None

    # Phase 2 Layout Control
    page_break_before: bool = False
    page_break_after: bool = False
    orientation: str | None = None

    # Phase 3 Content
    items: list[str] | None = None  # For static lists
    callout_type: str | None = None  # info, warning, success, danger
    metric: dict[str, Any] | None = None  # For metric cards
    columns_spec: list[TemplateSectionSpec] | None = (
        None  # For multi-column layouts - renamed to avoid conflict
    )
    code: str | None = None
    language: str | None = None
    quote_author: str | None = None

    # Phase 5 Data Processing
    filters: list[dict[str, Any]] | None = None
    sort: list[str] | None = None
    limit: int | None = None
    group_by: list[str] | None = None
    aggregations: dict[str, str] | None = None
    calculated_columns: dict[str, str] | None = None
    joins: list[dict[str, Any]] | None = None
    validation_rules: list[dict[str, Any]] | None = None
    show_totals: bool = False


class TemplateSpec(BaseModel):
    """Full template specification loaded from YAML.

    Attributes:
        name: Template name.
        description: Template description.
        version: Template version.
        sections: Ordered list of section specifications.
        metadata: Default document metadata.
        cover_page: Cover page configuration.
        page_layout: Page layout configuration.
        header: Page header configuration.
        footer: Page footer configuration.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    description: str | None = None
    version: str = "1.0"
    extends: str | None = None  # Parent template name
    sections: list[TemplateSectionSpec]

    # Phase 2 Enhancements
    metadata: dict[str, Any] | None = None
    cover_page: dict[str, Any] | None = None
    page_layout: dict[str, Any] | None = None
    header: dict[str, Any] | None = None
    footer: dict[str, Any] | None = None


# --- Theme Models ---


class FontSpec(BaseModel):
    """Font configuration for report rendering.

    Attributes:
        heading: Heading font family.
        body: Body text font family.
        monospace: Monospace font family.
        size_title: Title font size in points.
        size_heading: Heading font size in points.
        size_body: Body font size in points.
        size_caption: Caption font size in points.
    """

    model_config = ConfigDict(frozen=True)

    heading: str = "Arial"
    body: str = "Calibri"
    monospace: str = "Courier New"
    size_title: int = 24
    size_heading: int = 16
    size_body: int = 11
    size_caption: int = 9


class ColorSpec(BaseModel):
    """Color palette configuration for report rendering.

    Attributes:
        primary: Primary color hex.
        secondary: Secondary color hex.
        accent: Accent color hex.
        background: Background color hex.
        text: Main text color hex.
        text_light: Light text color hex.
        chart_palette: List of chart colors.
    """

    model_config = ConfigDict(frozen=True)

    primary: str = "#1a5276"
    secondary: str = "#2e86c1"
    accent: str = "#e74c3c"
    background: str = "#ffffff"
    text: str = "#2c3e50"
    text_light: str = "#7f8c8d"
    chart_palette: list[str] = [
        "#1a5276",
        "#2e86c1",
        "#85c1e9",
        "#e74c3c",
        "#2ecc71",
        "#f39c12",
        "#9b59b6",
        "#1abc9c",
    ]


class SpacingSpec(BaseModel):
    """Spacing and layout configuration.

    Attributes:
        section_gap_pt: Gap between sections in points.
        paragraph_gap_pt: Gap between paragraphs in points.
        page_margin_inches: Page margin in inches.
    """

    model_config = ConfigDict(frozen=True)

    section_gap_pt: int = 18
    paragraph_gap_pt: int = 6
    page_margin_inches: float = 1.0


class ChartThemeSpec(BaseModel):
    """Chart-specific theme configuration.

    Attributes:
        background_color: Chart background color hex.
        grid: Whether to show grid lines.
        grid_color: Grid line color hex.
        grid_alpha: Grid line opacity.
        title_size: Chart title font size.
        label_size: Axis label font size.
        tick_size: Tick label font size.
        legend_size: Legend font size.
        line_width: Default line width.
    """

    model_config = ConfigDict(frozen=True)

    background_color: str = "#ffffff"
    grid: bool = True
    grid_color: str = "#e0e0e0"
    grid_alpha: float = 0.5
    title_size: int = 14
    label_size: int = 11
    tick_size: int = 9
    legend_size: int = 10
    line_width: float = 2.0
    axis_line_color: str = "#333333"
    axis_line_width: float = 1.0
    tick_color: str = "#333333"
    tick_length: float = 4.0
    data_label_size: int = 9
    data_label_color: str = "#2c3e50"
    annotation_color: str = "#e74c3c"
    secondary_palette: list[str] = [
        "#95a5a6",
        "#7f8c8d",
        "#d35400",
        "#c0392b",
        "#bdc3c7",
    ]


class ThemeSpec(BaseModel):
    """Full theme specification loaded from YAML.

    Attributes:
        name: Theme name.
        description: Theme description.
        fonts: Font configuration.
        colors: Color palette configuration.
        spacing: Spacing and layout configuration.
        chart: Chart-specific theme configuration.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    description: str | None = None
    fonts: FontSpec = FontSpec()
    colors: ColorSpec = ColorSpec()
    spacing: SpacingSpec = SpacingSpec()
    chart: ChartThemeSpec = ChartThemeSpec()
