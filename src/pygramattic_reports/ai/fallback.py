"""Fallback generators for when Claude CLI is unavailable.

Produces basic, data-driven summaries without AI. Used as a
graceful degradation path when AI features are disabled or fail.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygramattic_reports.models import Dataset


def generate_fallback_summary(
    dataset: Dataset,
    report_title: str = "",
    max_words: int = 200,
) -> str:
    """Generate a basic summary without AI.

    Produces a data-driven summary using simple statistics
    and predefined templates. Used when Claude CLI is unavailable.

    Args:
        dataset: The source dataset.
        report_title: Report title for context.
        max_words: Approximate target length (advisory).

    Returns:
        A basic text summary.
    """
    _ = max_words  # Advisory limit; kept for API compatibility
    _ = report_title

    df = dataset.dataframe
    lines = [f"This report presents data from {dataset.name}."]
    lines.append(
        f"The dataset contains {dataset.row_count} records across {len(dataset.schema)} fields."
    )

    numeric_cols = df.select_dtypes(include="number").columns
    if len(numeric_cols) > 0:
        lines.append("\nKey statistics:")
        lines.extend(
            f"- {col}: min={df[col].min():.2f}, max={df[col].max():.2f}, avg={df[col].mean():.2f}"
            for col in numeric_cols[:5]
        )

    return "\n".join(lines)


def generate_fallback_narrative(
    dataset: Dataset,
    topic: str = "",
) -> str:
    """Generate a basic narrative without AI.

    Args:
        dataset: The source dataset.
        topic: Optional topic heading.

    Returns:
        A basic narrative string.
    """
    lines: list[str] = []
    if topic:
        lines.append(f"Analysis: {topic}")
    lines.append(f"\nThe dataset contains {dataset.row_count} records.")
    lines.append(f"Fields: {', '.join(dataset.column_names)}.")

    return "\n".join(lines)
