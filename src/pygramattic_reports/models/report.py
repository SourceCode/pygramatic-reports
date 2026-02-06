"""Report models for pygramattic-reports.

Defines the Report type -- the abstract report structure output by the
Builder, consumed by Output Adapters.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


class SectionType(StrEnum):
    """Types of report sections."""

    TITLE = "title"
    SUMMARY = "summary"
    NARRATIVE = "narrative"
    DATA_TABLE = "data_table"
    CHART = "chart"
    IMAGE = "image"
    HEADING = "heading"
    SPACER = "spacer"
    PAGE_BREAK = "page_break"
    # Phase 2
    TABLE_OF_CONTENTS = "table_of_contents"
    COVER_PAGE = "cover_page"
    # Phase 3
    LIST = "list"
    CALLOUT = "callout"
    METRIC_CARD = "metric_card"
    CODE_BLOCK = "code_block"
    QUOTE = "quote"
    COLUMNS = "columns"


class DocumentMetadata(BaseModel):
    """Metadata about the report document."""

    model_config = ConfigDict(frozen=True)

    title: str | None = None
    author: str | None = None
    subject: str | None = None
    keywords: list[str] = []
    version: str | None = None
    created_at: datetime | None = None


class PageLayout(BaseModel):
    """Page layout configuration."""

    model_config = ConfigDict(frozen=True)

    orientation: str = "portrait"  # "portrait", "landscape"
    margin_top_inches: float = 1.0
    margin_bottom_inches: float = 1.0
    margin_left_inches: float = 1.0
    margin_right_inches: float = 1.0
    page_numbers: bool = True


class RunningElement(BaseModel):
    """Header or footer template configuration."""

    model_config = ConfigDict(frozen=True)

    left: str | None = None
    center: str | None = None
    right: str | None = None
    font_size: int = 9


class CoverPageSpec(BaseModel):
    """Cover page configuration."""

    model_config = ConfigDict(frozen=True)

    title: str | None = None
    subtitle: str | None = None
    logo_path: str | None = None
    background_color: str | None = None
    show_date: bool = True
    custom_text: str | None = None


class ReportSection(BaseModel):
    """A single section of a rendered report.

    The Builder produces these. Output Adapters consume them.
    The content varies by section_type:
    - TITLE/HEADING/NARRATIVE/SUMMARY: text in ``content``
    - DATA_TABLE: dict with ``headers`` and ``rows`` keys in ``table_data``
    - CHART/IMAGE: raw bytes in ``media_bytes`` with ``media_type``
    - SPACER/PAGE_BREAK: structural markers (no content)

    Attributes:
        section_type: The type of this section.
        title: Section heading if applicable.
        content: Text content for text-based sections.
        table_data: Table data for DATA_TABLE sections.
        media_bytes: Raw image data for CHART/IMAGE sections.
        media_type: MIME type of the media.
        media_path: Path to saved media file.
        level: Heading level (1-6).
        metadata: Additional section-specific metadata.
    """

    model_config = ConfigDict(frozen=True)

    section_type: SectionType
    title: str | None = None
    content: str | None = None
    table_data: dict[str, Any] | None = None
    media_bytes: bytes | None = None
    media_type: str | None = None
    media_path: str | None = None
    level: int = 1
    metadata: dict[str, Any] = {}

    # Phase 3 Layout Data
    list_data: list[str] | list[dict[str, Any]] | None = None
    card_data: dict[str, Any] | None = None
    callout_data: dict[str, str] | None = None
    code_data: dict[str, str] | None = None  # {language, code}
    quote_data: dict[str, str] | None = None  # {text, author}
    columns_data: list[ReportSection] | None = None  # Nested sections


class NumberClaim(BaseModel):
    """A numerical value in the report that can be validated against source data.

    The Builder emits these during assembly so the Validator can check them
    without re-parsing the output document.

    Attributes:
        section_index: Which section contains this claim.
        value: The numeric value.
        formatted_value: How it appears in the report.
        source_dataset_id: Which dataset it came from.
        source_column: Which column.
        computation: How it was derived.
        description: Human-readable description.
    """

    model_config = ConfigDict(frozen=True)

    section_index: int
    value: float
    formatted_value: str
    source_dataset_id: str
    source_column: str
    computation: str
    description: str


class Report(BaseModel):
    """A fully assembled report, ready for output formatting.

    This is the output of the Builder and the input to Output Adapters.
    It is format-agnostic -- it describes what the report contains, not
    how it is rendered in any specific format.

    Attributes:
        id: Unique report identifier.
        name: Report name.
        sections: Ordered list of report sections.
        number_claims: Numeric claims for validation.
        datasets_used: Dataset IDs referenced by this report.
        template_name: Name of the template used.
        theme_name: Name of the theme applied.
        build_timestamp: When the report was built.
        build_warnings: Non-fatal issues encountered during build.
        metadata: Document-level metadata.
        page_layout: Page layout settings.
        cover_page: Optional cover page configuration.
        header: Optional page header configuration.
        footer: Optional page footer configuration.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    sections: list[ReportSection]
    number_claims: list[NumberClaim] = []
    datasets_used: list[str] = []
    template_name: str
    theme_name: str
    build_timestamp: datetime
    build_warnings: list[str] = []

    # Phase 2 Enhancements
    metadata: DocumentMetadata | None = None
    page_layout: PageLayout = PageLayout()
    cover_page: CoverPageSpec | None = None
    header: RunningElement | None = None
    footer: RunningElement | None = None
