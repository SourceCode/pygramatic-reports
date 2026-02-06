"""JSON converter for Dataset objects.

Supports two output layouts (records and columnar) with type-aware
serialization, deterministic ordering, and configurable formatting.
"""

from __future__ import annotations

import json
import math
from typing import TYPE_CHECKING, Any

from pygramattic_reports.exceptions import ConversionError
from pygramattic_reports.models.dataset import DataType

if TYPE_CHECKING:
    from pygramattic_reports.models.dataset import ColumnSchema, Dataset

_VALID_LAYOUTS = frozenset({"records", "columnar"})


def to_json(
    dataset: Dataset,
    layout: str = "records",
    indent: int | None = 2,
    sort_keys: bool = True,
) -> str:
    """Convert a Dataset to a JSON string.

    Args:
        dataset: The source dataset.
        layout: Output structure (``"records"`` or ``"columnar"``).
        indent: JSON indentation level (``None`` for compact).
        sort_keys: Sort object keys alphabetically.

    Returns:
        JSON string representation of the dataset.

    Raises:
        ConversionError: If serialization fails.
    """
    if layout not in _VALID_LAYOUTS:
        msg = f"Invalid layout {layout!r}, expected 'records' or 'columnar'"
        raise ConversionError(msg)

    try:
        data = _to_records(dataset) if layout == "records" else _to_columnar(dataset)
        return json.dumps(data, indent=indent, sort_keys=sort_keys, default=str)
    except ConversionError:
        raise
    except Exception as exc:
        msg = f"Failed to convert dataset to JSON: {exc}"
        raise ConversionError(msg) from exc


def _to_records(dataset: Dataset) -> list[dict[str, Any]]:
    """Convert dataset to records layout (array of objects)."""
    schema_map = {col.name: col for col in dataset.schema}
    records: list[dict[str, Any]] = []

    for _, row in dataset.dataframe.iterrows():
        record: dict[str, Any] = {}
        for col_name in dataset.column_names:
            col_schema = schema_map.get(col_name)
            value = row.get(col_name)
            record[col_name] = _serialize_value(value, col_schema)
        records.append(record)

    return records


def _to_columnar(dataset: Dataset) -> dict[str, list[Any]]:
    """Convert dataset to columnar layout (object of arrays)."""
    schema_map = {col.name: col for col in dataset.schema}
    columns: dict[str, list[Any]] = {}

    for col_name in dataset.column_names:
        col_schema = schema_map.get(col_name)
        columns[col_name] = [
            _serialize_value(v, col_schema) for v in dataset.dataframe[col_name]
        ]

    return columns


def _serialize_value(
    value: object,
    col_schema: ColumnSchema | None,
) -> object:
    """Serialize a single value based on its column schema type.

    Returns:
        JSON-compatible Python value.
    """
    if _is_null(value):
        return None

    if col_schema is None:
        return value

    dtype = col_schema.dtype

    if dtype == DataType.INTEGER:
        return int(value)  # type: ignore[call-overload]

    if dtype == DataType.FLOAT:
        return float(value)  # type: ignore[arg-type]

    if dtype == DataType.BOOLEAN:
        return value if isinstance(value, bool) else str(value).lower() in ("true", "1", "yes")

    # STRING, DATE, DATETIME all serialize as str
    return str(value)


def _is_null(value: object) -> bool:
    """Check if a value should be serialized as JSON null."""
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
