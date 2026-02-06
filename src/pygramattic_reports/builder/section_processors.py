"""Section processors for the report builder.

Processing functions for each section type. The builder dispatches
to these based on ``section_spec.source``.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from pygramattic_reports.models import (
    ChartSpec,
    ChartType,
    NumberClaim,
    ReportSection,
    SectionType,
)

if TYPE_CHECKING:
    from pygramattic_reports.charts import ChartEngine
    from pygramattic_reports.models import (
        Dataset,
        TemplateSectionSpec,
        ThemeSpec,
    )


# -- Public section-type map --------------------------------------------------

_SECTION_TYPE_MAP: dict[str, SectionType] = {
    "title": SectionType.TITLE,
    "heading": SectionType.HEADING,
    "summary": SectionType.SUMMARY,
    "narrative": SectionType.NARRATIVE,
    "data_table": SectionType.DATA_TABLE,
    "chart": SectionType.CHART,
    "image": SectionType.IMAGE,
    "spacer": SectionType.SPACER,
    "page_break": SectionType.PAGE_BREAK,
    "table_of_contents": SectionType.TABLE_OF_CONTENTS,
}


def map_section_type(type_str: str) -> SectionType:
    """Map a template section type string to a SectionType enum.

    Args:
        type_str: Template section type string.

    Returns:
        Corresponding SectionType.
    """
    return _SECTION_TYPE_MAP.get(type_str, SectionType.NARRATIVE)


# -- Section processors -------------------------------------------------------


def process_static_section(
    spec: TemplateSectionSpec,
) -> tuple[ReportSection, list[NumberClaim]]:
    """Process a static content section.

    Handles title, heading, narrative, page_break, and other
    static-source sections.

    Args:
        spec: Template section specification.

    Returns:
        Tuple of (ReportSection, empty NumberClaim list).
    """
    section_type = map_section_type(spec.type)
    return (
        ReportSection(
            section_type=section_type,
            title=spec.title,
            content=spec.content,
            level=spec.level,
        ),
        [],
    )


def process_data_table_section(
    spec: TemplateSectionSpec,
    dataset: Dataset,
    section_index: int,
) -> tuple[ReportSection, list[NumberClaim]]:
    """Process a data table section.

    Extracts the requested columns from the dataset and formats
    as a table structure (headers + rows). Generates NumberClaims
    for numeric values so the validator can check them.

    Args:
        spec: Template section specification.
        dataset: Source dataset.
        section_index: Index of this section in the report.

    Returns:
        Tuple of (ReportSection, list of NumberClaims).
    """
    columns = spec.columns or dataset.column_names
    df = dataset.dataframe[columns]

    headers = list(df.columns)
    rows = df.values.tolist()

    claims = _generate_number_claims(
        headers, rows, dataset, section_index,
    )

    return (
        ReportSection(
            section_type=SectionType.DATA_TABLE,
            title=spec.title,
            table_data={"headers": headers, "rows": rows},
        ),
        claims,
    )


def process_chart_section(
    spec: TemplateSectionSpec,
    dataset: Dataset,
    theme: ThemeSpec,
    chart_engine: ChartEngine,
) -> tuple[ReportSection, list[NumberClaim]]:
    """Process a chart section.

    Builds a ChartSpec from the template section spec, generates
    the chart using the chart engine, and returns the image bytes.

    Args:
        spec: Template section specification.
        dataset: Source dataset.
        theme: Theme for styling.
        chart_engine: Chart engine instance.

    Returns:
        Tuple of (ReportSection with image bytes, empty claims).

    Raises:
        ChartError: If chart rendering fails.
    """
    chart_spec = ChartSpec(
        chart_type=ChartType(spec.chart_type or "bar"),
        title=spec.title or "Chart",
        x_column=spec.x_column or "",
        y_columns=spec.y_columns or [],
        dataset_id=dataset.id,
    )

    image_bytes = chart_engine.generate(chart_spec, dataset, theme)

    return (
        ReportSection(
            section_type=SectionType.CHART,
            title=spec.title,
            media_bytes=image_bytes,
            media_type=f"image/{chart_spec.output_format.value}",
        ),
        [],
    )


def process_ai_placeholder_section(
    spec: TemplateSectionSpec,
) -> tuple[ReportSection, list[NumberClaim]]:
    """Placeholder for AI-generated sections (until Phase 18).

    Returns a section with a placeholder message indicating
    AI content would be generated here.

    Args:
        spec: Template section specification.

    Returns:
        Tuple of (ReportSection with placeholder, empty claims).
    """
    prompt_text = spec.ai_prompt or "No prompt specified"
    return (
        ReportSection(
            section_type=map_section_type(spec.type),
            title=spec.title,
            content=f"[AI-generated content placeholder: {prompt_text}]",
            metadata={
                "ai_placeholder": True,
                "ai_prompt": spec.ai_prompt,
            },
        ),
        [],
    )


# -- Helpers ------------------------------------------------------------------


def _generate_number_claims(
    headers: list[str],
    rows: list[list[object]],
    dataset: Dataset,
    section_index: int,
) -> list[NumberClaim]:
    """Generate NumberClaims for numeric columns in a data table."""
    claims: list[NumberClaim] = []

    for col_idx, col_name in enumerate(headers):
        col_schema = next(
            (c for c in dataset.schema if c.name == col_name), None,
        )
        if col_schema is None or col_schema.dtype not in ("int", "float"):
            continue

        for row_idx, row in enumerate(rows):
            val = row[col_idx]
            if val is None:
                continue
            fval = float(val)  # type: ignore[arg-type]
            if math.isnan(fval):
                continue
            claims.append(
                NumberClaim(
                    section_index=section_index,
                    value=fval,
                    formatted_value=str(val),
                    source_dataset_id=dataset.id,
                    source_column=col_name,
                    computation=f"raw[{row_idx}]",
                    description=f"{col_name} row {row_idx}",
                ),
            )

    return claims
