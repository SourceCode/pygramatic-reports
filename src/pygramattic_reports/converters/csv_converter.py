"""CSV converter for Dataset objects.

Converts a Dataset back to CSV format using Python's csv module
for correct quoting and escaping.
"""

from __future__ import annotations

import csv
import io
import math
from typing import TYPE_CHECKING

from pygramattic_reports.exceptions import ConversionError

if TYPE_CHECKING:
    from pygramattic_reports.models.dataset import Dataset


def to_csv(
    dataset: Dataset,
    delimiter: str = ",",
    include_header: bool = True,
) -> str:
    """Convert a Dataset to CSV format.

    Args:
        dataset: The source dataset.
        delimiter: Field delimiter character.
        include_header: Whether to include a header row.

    Returns:
        CSV string.

    Raises:
        ConversionError: If conversion fails.
    """
    try:
        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter, lineterminator="\n")

        if include_header:
            writer.writerow(dataset.column_names)

        for _, row in dataset.dataframe.iterrows():
            values: list[str] = []
            for col_name in dataset.column_names:
                value = row.get(col_name)
                values.append(_format_value(value))
            writer.writerow(values)

        return output.getvalue()
    except ConversionError:
        raise
    except Exception as exc:
        msg = f"Failed to convert dataset to CSV: {exc}"
        raise ConversionError(msg) from exc


def _format_value(value: object) -> str:
    """Format a value for CSV output."""
    if _is_null(value):
        return ""
    return str(value)


def _is_null(value: object) -> bool:
    """Check if a value should be rendered as empty in CSV."""
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    try:
        import pandas as pd  # noqa: PLC0415

        if pd.isna(value):  # type: ignore[call-overload]
            return True
    except (TypeError, ValueError):
        pass
    return False
