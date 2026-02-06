"""Tabular data normalizer with schema inference and type coercion."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

import pandas as pd

from pygramattic_reports.exceptions import NormalizationError
from pygramattic_reports.logging import get_logger
from pygramattic_reports.models import ColumnSchema, ContentType, DataType, Provenance
from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.models.dataset import Dataset

from .base import BaseNormalizer

if TYPE_CHECKING:
    from pygramattic_reports.models import RawData

_logger = get_logger("normalizers.tabular")

_NULL_STRINGS = frozenset({"", "null", "none", "n/a", "na", "nan"})
_BOOLEAN_TRUE = frozenset({"true", "1", "yes"})
_BOOLEAN_FALSE = frozenset({"false", "0", "no"})
_BOOLEAN_VALUES = _BOOLEAN_TRUE | _BOOLEAN_FALSE
_DATE_FORMATS = ("%m/%d/%Y", "%Y/%m/%d")


class TabularNormalizer(BaseNormalizer):
    """Normalizes tabular raw data into typed Dataset objects.

    Handles schema inference, type coercion, null detection, and
    DataFrame creation for row/column data from CSV, JSON arrays,
    or any other tabular source.
    """

    def normalize(self, raw_data: RawData) -> Dataset:
        """Normalize tabular RawData into a Dataset.

        Args:
            raw_data: Raw data with ``content_type=TABULAR``.

        Returns:
            Dataset with inferred schema and typed DataFrame.

        Raises:
            NormalizationError: If the data is not tabular or cannot
                be normalized.
        """
        if raw_data.content_type != ContentType.TABULAR:
            msg = f"Expected tabular data, got {raw_data.content_type}"
            raise NormalizationError(msg)

        headers = raw_data.tabular_headers or []
        rows = raw_data.tabular_data or []

        if not headers:
            return self._build_empty_dataset(raw_data)

        columns = _extract_columns(headers, rows)
        schema = _infer_schema(headers, columns)
        df = _build_dataframe(headers, columns, schema)

        _logger.info(
            "Normalized tabular data",
            rows=len(df),
            columns=len(headers),
            types={cs.name: cs.dtype.value for cs in schema},
        )

        return Dataset(
            id=generate_id(),
            name=raw_data.source_config.name,
            schema=schema,
            dataframe=df,
            provenance=_build_provenance(raw_data),
        )

    @staticmethod
    def _build_empty_dataset(raw_data: RawData) -> Dataset:
        """Build an empty Dataset for data with no columns."""
        return Dataset(
            id=generate_id(),
            name=raw_data.source_config.name,
            schema=[],
            dataframe=pd.DataFrame(),
            provenance=_build_provenance(raw_data),
        )


def _build_provenance(raw_data: RawData) -> Provenance:
    """Build provenance from RawData source info."""
    return Provenance(
        source_type=raw_data.source_config.source_type.value,
        source_name=raw_data.source_config.name,
        source_path=(
            str(raw_data.source_config.file.path)
            if raw_data.source_config.file
            else None
        ),
        loaded_at=raw_data.loaded_at,
        normalized_at=now_utc(),
        row_count_raw=raw_data.row_count or 0,
    )


def _extract_columns(
    headers: list[str],
    rows: list[dict[str, Any]],
) -> dict[str, list[Any]]:
    """Extract column value lists from row dicts."""
    return {header: [row.get(header) for row in rows] for header in headers}


def _infer_schema(
    headers: list[str],
    columns: dict[str, list[Any]],
) -> list[ColumnSchema]:
    """Infer ColumnSchema for each column."""
    schema: list[ColumnSchema] = []
    for header in headers:
        values = columns[header]
        dtype = _infer_column_type(values)
        has_nulls = any(_is_null(v) for v in values)
        schema.append(ColumnSchema(name=header, dtype=dtype, nullable=has_nulls))
    return schema


def _build_dataframe(
    headers: list[str],
    columns: dict[str, list[Any]],
    schema: list[ColumnSchema],
) -> pd.DataFrame:
    """Build a pandas DataFrame with coerced column values."""
    df_data: dict[str, list[Any]] = {}
    for header, col_schema in zip(headers, schema, strict=True):
        df_data[header] = _coerce_column(columns[header], col_schema.dtype)
    return pd.DataFrame(df_data)


def _is_null(value: Any) -> bool:  # noqa: ANN401
    """Check if a value represents null."""
    if value is None:
        return True
    return isinstance(value, str) and value.strip().lower() in _NULL_STRINGS


def _infer_column_type(values: list[Any]) -> DataType:
    """Infer the best DataType for a column based on its values.

    Strategy: try to parse as each type in order of specificity.
    Most specific wins (boolean > integer > float > date > string).

    Args:
        values: All values in the column.

    Returns:
        The inferred DataType.
    """
    non_null = [v for v in values if not _is_null(v)]
    if not non_null:
        return DataType.STRING

    str_values = [str(v).strip() for v in non_null]

    if all(v.lower() in _BOOLEAN_VALUES for v in str_values):
        return DataType.BOOLEAN

    if all(_is_integer(v) for v in str_values):
        return DataType.INTEGER

    if all(_is_float(v) for v in str_values):
        return DataType.FLOAT

    if all(_is_date(v) for v in str_values):
        return DataType.DATE

    return DataType.STRING


def _is_integer(value: str) -> bool:
    """Check if a string can be parsed as an integer."""
    try:
        int(value)
    except (ValueError, OverflowError):
        return False
    else:
        return True


def _is_float(value: str) -> bool:
    """Check if a string can be parsed as a float."""
    try:
        float(value)
    except (ValueError, OverflowError):
        return False
    else:
        return True


def _is_date(value: str) -> bool:
    """Check if a string can be parsed as a date."""
    return _try_parse_date(value) is not None


def _try_parse_date(value: str) -> datetime | None:
    """Attempt to parse a string as a date."""
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)  # noqa: DTZ007
        except ValueError:
            continue
    return None


def _coerce_column(values: list[Any], dtype: DataType) -> list[Any]:
    """Coerce all values in a column to the target type."""
    return [_coerce_value(v, dtype) for v in values]


def _coerce_value(value: Any, dtype: DataType) -> Any:  # noqa: ANN401
    """Coerce a single value to the target type.

    Returns None for null values.
    """
    if _is_null(value):
        return None

    str_val = str(value).strip()

    if dtype == DataType.BOOLEAN:
        return str_val.lower() in _BOOLEAN_TRUE
    if dtype == DataType.INTEGER:
        return int(str_val)
    if dtype == DataType.FLOAT:
        return float(str_val)
    if dtype == DataType.DATE:
        return _try_parse_date(str_val)
    return str_val
