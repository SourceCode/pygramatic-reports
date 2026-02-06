"""Tests for the data converters (Phase 9)."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from pygramattic_reports.converters import to_csv, to_json, to_sql
from pygramattic_reports.exceptions import ConversionError
from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.models.dataset import ColumnSchema, Dataset, DataType, Provenance

# ---------- Helpers ----------------------------------------------------------


def _make_dataset(
    data: dict[str, list[object]],
    schema: list[ColumnSchema],
    name: str = "test_data",
) -> Dataset:
    """Build a Dataset from column data and schema."""
    df = pd.DataFrame(data)
    return Dataset(
        id=generate_id(),
        name=name,
        schema=schema,
        dataframe=df,
        provenance=Provenance(
            source_type="test",
            source_name="test",
            loaded_at=now_utc(),
            normalized_at=now_utc(),
            row_count_raw=len(df),
        ),
    )


def _simple_dataset() -> Dataset:
    """Create a basic test dataset with several column types."""
    return _make_dataset(
        data={
            "name": ["Alice", "Bob", "Charlie"],
            "score": [95, 82, 70],
            "grade": [3.9, 3.2, 2.8],
            "active": [True, False, True],
        },
        schema=[
            ColumnSchema(name="name", dtype=DataType.STRING, nullable=False),
            ColumnSchema(name="score", dtype=DataType.INTEGER, nullable=False),
            ColumnSchema(name="grade", dtype=DataType.FLOAT, nullable=False),
            ColumnSchema(name="active", dtype=DataType.BOOLEAN, nullable=False),
        ],
    )


# ---------- JSON converter tests ---------------------------------------------


class TestJsonRecordsLayout:
    """Test default (records) JSON layout."""

    def test_to_json_records_layout(self) -> None:
        """Default layout produces array of objects."""
        ds = _simple_dataset()
        result = to_json(ds)
        parsed = json.loads(result)

        assert isinstance(parsed, list)
        assert len(parsed) == 3
        assert parsed[0]["name"] == "Alice"
        assert parsed[0]["score"] == 95
        assert parsed[0]["grade"] == 3.9
        assert parsed[0]["active"] is True

    def test_to_json_deterministic(self) -> None:
        """Same input always produces same output."""
        ds = _simple_dataset()
        result1 = to_json(ds)
        result2 = to_json(ds)
        assert result1 == result2

    def test_to_json_compact(self) -> None:
        """No indentation when indent=None."""
        ds = _simple_dataset()
        result = to_json(ds, indent=None)
        assert "\n" not in result


class TestJsonColumnarLayout:
    """Test columnar JSON layout."""

    def test_to_json_columnar_layout(self) -> None:
        """Columnar layout produces object of arrays."""
        ds = _simple_dataset()
        result = to_json(ds, layout="columnar")
        parsed = json.loads(result)

        assert isinstance(parsed, dict)
        assert parsed["name"] == ["Alice", "Bob", "Charlie"]
        assert parsed["score"] == [95, 82, 70]
        assert parsed["active"] == [True, False, True]


class TestJsonDateSerialization:
    """Test date type serialization."""

    def test_to_json_date_serialization(self) -> None:
        """Dates serialized as ISO 8601 strings."""
        ds = _make_dataset(
            data={"event": ["2024-01-15", "2024-06-30"]},
            schema=[ColumnSchema(name="event", dtype=DataType.DATE)],
        )
        result = to_json(ds)
        parsed = json.loads(result)
        assert parsed[0]["event"] == "2024-01-15"
        assert parsed[1]["event"] == "2024-06-30"


class TestJsonNullHandling:
    """Test null/NaN serialization."""

    def test_to_json_null_handling(self) -> None:
        """NaN/None serialized as null."""
        ds = _make_dataset(
            data={"value": [1.0, float("nan"), None]},
            schema=[ColumnSchema(name="value", dtype=DataType.FLOAT, nullable=True)],
        )
        result = to_json(ds)
        parsed = json.loads(result)
        assert parsed[0]["value"] == 1.0
        assert parsed[1]["value"] is None
        assert parsed[2]["value"] is None


class TestJsonInvalidLayout:
    """Test error handling for invalid layout."""

    def test_invalid_layout_raises(self) -> None:
        """Invalid layout raises ConversionError."""
        ds = _simple_dataset()
        with pytest.raises(ConversionError, match="Invalid layout"):
            to_json(ds, layout="invalid")


# ---------- SQL converter tests ----------------------------------------------


class TestSqlPostgresql:
    """Test PostgreSQL dialect."""

    def test_to_sql_postgresql(self) -> None:
        """Correct DDL for PostgreSQL types."""
        ds = _simple_dataset()
        result = to_sql(ds, dialect="postgresql")

        assert "CREATE TABLE test_data" in result
        assert "name TEXT NOT NULL" in result
        assert "score INTEGER NOT NULL" in result
        assert "grade DOUBLE PRECISION NOT NULL" in result
        assert "active BOOLEAN NOT NULL" in result
        assert "INSERT INTO test_data" in result
        assert "'Alice'" in result


class TestSqlSqlite:
    """Test SQLite dialect."""

    def test_to_sql_sqlite(self) -> None:
        """Correct DDL for SQLite types."""
        ds = _simple_dataset()
        result = to_sql(ds, dialect="sqlite")

        assert "CREATE TABLE test_data" in result
        assert "grade REAL NOT NULL" in result
        assert "INSERT INTO test_data" in result


class TestSqlDropTable:
    """Test DROP TABLE IF EXISTS prefix."""

    def test_to_sql_with_drop(self) -> None:
        """Includes DROP TABLE IF EXISTS when requested."""
        ds = _simple_dataset()
        result = to_sql(ds, drop_existing=True)

        assert "DROP TABLE IF EXISTS test_data;" in result
        assert result.index("DROP TABLE") < result.index("CREATE TABLE")


class TestSqlNullValues:
    """Test NULL handling in INSERT statements."""

    def test_to_sql_null_values(self) -> None:
        """NULL handled correctly in INSERTs."""
        ds = _make_dataset(
            data={"value": [1.0, float("nan"), None]},
            schema=[ColumnSchema(name="value", dtype=DataType.FLOAT, nullable=True)],
        )
        result = to_sql(ds)
        assert "NULL" in result
        assert "1.0" in result


class TestSqlStringEscaping:
    """Test single-quote escaping in SQL."""

    def test_to_sql_string_escaping(self) -> None:
        """Single quotes escaped properly."""
        ds = _make_dataset(
            data={"text": ["it's a test", "normal"]},
            schema=[ColumnSchema(name="text", dtype=DataType.STRING)],
        )
        result = to_sql(ds)
        assert "'it''s a test'" in result


class TestSqlTableNameSanitization:
    """Test table name sanitization."""

    def test_to_sql_table_name_sanitization(self) -> None:
        """Invalid chars removed from table name."""
        ds = _make_dataset(
            data={"x": [1]},
            schema=[ColumnSchema(name="x", dtype=DataType.INTEGER)],
            name="My Data! (2024)",
        )
        result = to_sql(ds)
        assert "CREATE TABLE my_data_2024" in result

    def test_to_sql_numeric_start(self) -> None:
        """Table names starting with digits get t_ prefix."""
        ds = _make_dataset(
            data={"x": [1]},
            schema=[ColumnSchema(name="x", dtype=DataType.INTEGER)],
            name="123data",
        )
        result = to_sql(ds)
        assert "CREATE TABLE t_123data" in result


class TestSqlBatchInserts:
    """Test batch INSERT statement generation."""

    def test_to_sql_batch_inserts(self) -> None:
        """Large datasets split into batches."""
        ds = _make_dataset(
            data={"val": list(range(250))},
            schema=[ColumnSchema(name="val", dtype=DataType.INTEGER)],
        )
        result = to_sql(ds, batch_size=100)
        insert_count = result.count("INSERT INTO")
        assert insert_count == 3


class TestSqlInvalidDialect:
    """Test error handling for invalid dialect."""

    def test_invalid_dialect_raises(self) -> None:
        """Invalid dialect raises ConversionError."""
        ds = _simple_dataset()
        with pytest.raises(ConversionError, match="Invalid dialect"):
            to_sql(ds, dialect="oracle")


# ---------- CSV converter tests ----------------------------------------------


class TestCsvBasic:
    """Test standard CSV output."""

    def test_to_csv_basic(self) -> None:
        """Standard CSV output with header and data rows."""
        ds = _simple_dataset()
        result = to_csv(ds)
        lines = result.strip().split("\n")

        assert lines[0] == "name,score,grade,active"
        assert lines[1] == "Alice,95,3.9,True"
        assert len(lines) == 4


class TestCsvCustomDelimiter:
    """Test semicolon delimiter."""

    def test_to_csv_custom_delimiter(self) -> None:
        """Semicolon delimiter works."""
        ds = _simple_dataset()
        result = to_csv(ds, delimiter=";")
        lines = result.strip().split("\n")

        assert lines[0] == "name;score;grade;active"
        assert ";" in lines[1]


class TestCsvSpecialCharacters:
    """Test values with commas, quotes, and newlines."""

    def test_to_csv_special_characters(self) -> None:
        """Values with commas, quotes, newlines are escaped."""
        ds = _make_dataset(
            data={"text": ["has, comma", 'has "quotes"', "has\nnewline"]},
            schema=[ColumnSchema(name="text", dtype=DataType.STRING)],
        )
        result = to_csv(ds)
        # csv module wraps values containing special chars in quotes
        assert '"has, comma"' in result
        assert '"has ""quotes"""' in result
        assert '"has\nnewline"' in result
