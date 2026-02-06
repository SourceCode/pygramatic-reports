"""SQL converter for Dataset objects.

Generates CREATE TABLE DDL and INSERT DML statements for
PostgreSQL and SQLite dialects.
"""

from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING

from pygramattic_reports.exceptions import ConversionError
from pygramattic_reports.models.dataset import DataType

if TYPE_CHECKING:
    from pygramattic_reports.models.dataset import ColumnSchema, Dataset

_VALID_DIALECTS = frozenset({"postgresql", "sqlite"})

_TYPE_MAP_POSTGRESQL: dict[DataType, str] = {
    DataType.STRING: "TEXT",
    DataType.INTEGER: "INTEGER",
    DataType.FLOAT: "DOUBLE PRECISION",
    DataType.DATE: "DATE",
    DataType.DATETIME: "TIMESTAMP",
    DataType.BOOLEAN: "BOOLEAN",
}

_TYPE_MAP_SQLITE: dict[DataType, str] = {
    DataType.STRING: "TEXT",
    DataType.INTEGER: "INTEGER",
    DataType.FLOAT: "REAL",
    DataType.DATE: "DATE",
    DataType.DATETIME: "TIMESTAMP",
    DataType.BOOLEAN: "BOOLEAN",
}

_SANITIZE_RE = re.compile(r"[^a-zA-Z0-9_]")


def to_sql(
    dataset: Dataset,
    dialect: str = "postgresql",
    table_name: str | None = None,
    drop_existing: bool = False,
    batch_size: int = 100,
) -> str:
    """Convert a Dataset to SQL DDL + INSERT statements.

    Args:
        dataset: The source dataset.
        dialect: SQL dialect (``"postgresql"`` or ``"sqlite"``).
        table_name: Override table name (defaults to ``dataset.name``).
        drop_existing: Include ``DROP TABLE IF EXISTS``.
        batch_size: Maximum rows per INSERT statement.

    Returns:
        SQL string with CREATE TABLE and INSERT statements.

    Raises:
        ConversionError: If conversion fails.
    """
    if dialect not in _VALID_DIALECTS:
        msg = f"Invalid dialect {dialect!r}, expected 'postgresql' or 'sqlite'"
        raise ConversionError(msg)

    try:
        name = _sanitize_table_name(table_name or dataset.name)
        type_map = _TYPE_MAP_POSTGRESQL if dialect == "postgresql" else _TYPE_MAP_SQLITE

        parts: list[str] = []

        if drop_existing:
            parts.append(f"DROP TABLE IF EXISTS {name};\n")

        parts.append(_create_table(name, dataset.schema, type_map))

        if dataset.row_count > 0:
            parts.extend(
                _insert_statements(name, dataset, batch_size)
            )

        return "\n".join(parts) + "\n"
    except ConversionError:
        raise
    except Exception as exc:
        msg = f"Failed to convert dataset to SQL: {exc}"
        raise ConversionError(msg) from exc


def _sanitize_table_name(name: str) -> str:
    """Sanitize a string for use as a SQL table name."""
    sanitized = _SANITIZE_RE.sub("_", name.strip().lower())
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")
    if not sanitized:
        return "dataset"
    if sanitized[0].isdigit():
        sanitized = "t_" + sanitized
    return sanitized


def _create_table(
    name: str,
    schema: list[ColumnSchema],
    type_map: dict[DataType, str],
) -> str:
    """Generate a CREATE TABLE statement."""
    col_defs: list[str] = []
    for col in schema:
        sql_type = type_map.get(col.dtype, "TEXT")
        null_constraint = "" if col.nullable else " NOT NULL"
        col_defs.append(f"    {col.name} {sql_type}{null_constraint}")

    columns = ",\n".join(col_defs)
    return f"CREATE TABLE {name} (\n{columns}\n);\n"


def _insert_statements(
    name: str,
    dataset: Dataset,
    batch_size: int,
) -> list[str]:
    """Generate INSERT INTO statements in batches."""
    col_names = ", ".join(dataset.column_names)
    schema_map = {col.name: col for col in dataset.schema}
    statements: list[str] = []

    rows: list[str] = []
    for _, row in dataset.dataframe.iterrows():
        values: list[str] = []
        for col_name in dataset.column_names:
            col_schema = schema_map.get(col_name)
            value = row.get(col_name)
            values.append(_format_sql_value(value, col_schema))
        rows.append(f"    ({', '.join(values)})")

        if len(rows) >= batch_size:
            stmt = f"INSERT INTO {name} ({col_names}) VALUES\n"
            stmt += ",\n".join(rows) + ";"
            statements.append(stmt)
            rows = []

    if rows:
        stmt = f"INSERT INTO {name} ({col_names}) VALUES\n"
        stmt += ",\n".join(rows) + ";"
        statements.append(stmt)

    return statements


def _format_sql_value(value: object, col_schema: ColumnSchema | None) -> str:
    """Format a single value as a SQL literal."""
    if _is_null(value):
        return "NULL"

    if col_schema is None:
        return _escape_string(str(value))

    dtype = col_schema.dtype

    if dtype == DataType.INTEGER:
        return str(int(value))  # type: ignore[call-overload]

    if dtype == DataType.FLOAT:
        return str(float(value))  # type: ignore[arg-type]

    if dtype == DataType.BOOLEAN:
        is_true = value if isinstance(value, bool) else str(value).lower() in ("true", "1", "yes")
        return "TRUE" if is_true else "FALSE"

    # STRING, DATE, DATETIME all use quoted string
    return _escape_string(str(value))


def _escape_string(value: str) -> str:
    """Escape a string value for SQL, wrapping in single quotes."""
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


def _is_null(value: object) -> bool:
    """Check if a value should be rendered as SQL NULL."""
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
