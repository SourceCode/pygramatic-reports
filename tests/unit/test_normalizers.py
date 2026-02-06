"""Unit tests for data normalizers."""

from __future__ import annotations

from pathlib import Path

import pytest

from pygramattic_reports.exceptions import NormalizationError
from pygramattic_reports.models import (
    ContentType,
    DataType,
    FileSourceConfig,
    RawData,
    SourceConfig,
    SourceType,
)
from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.normalizers import TabularNormalizer


def _make_raw_data(
    headers: list[str],
    rows: list[dict[str, object]],
    *,
    name: str = "test_data",
) -> RawData:
    """Build a RawData object for testing."""
    return RawData(
        id=generate_id(),
        source_config=SourceConfig(
            source_type=SourceType.CSV,
            name=name,
            file=FileSourceConfig(path=Path("/test/data.csv")),
        ),
        content_type=ContentType.TABULAR,
        tabular_data=rows,
        tabular_headers=headers,
        row_count=len(rows),
        loaded_at=now_utc(),
    )


# ---- Basic Normalization ----


class TestTabularNormalizerCsvData:
    def test_normalizes_csv_data(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["region", "revenue"],
            rows=[
                {"region": "US", "revenue": "1500.50"},
                {"region": "EU", "revenue": "2300.75"},
            ],
        )
        dataset = normalizer.normalize(raw)

        assert dataset.name == "test_data"
        assert dataset.row_count == 2
        assert list(dataset.dataframe.columns) == ["region", "revenue"]
        assert dataset.dataframe["region"].tolist() == ["US", "EU"]

    def test_rejects_non_tabular(self):
        raw = RawData(
            id=generate_id(),
            source_config=SourceConfig(
                source_type=SourceType.JSON,
                name="doc",
                file=FileSourceConfig(path=Path("/test/doc.json")),
            ),
            content_type=ContentType.DOCUMENT,
            document_text=["some text"],
            loaded_at=now_utc(),
        )
        normalizer = TabularNormalizer()
        with pytest.raises(NormalizationError, match="Expected tabular"):
            normalizer.normalize(raw)


# ---- Type Inference ----


class TestTypeInferenceInteger:
    def test_integer_column(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["count"],
            rows=[{"count": "10"}, {"count": "20"}, {"count": "30"}],
        )
        dataset = normalizer.normalize(raw)

        col = next(c for c in dataset.schema if c.name == "count")
        assert col.dtype == DataType.INTEGER
        assert dataset.dataframe["count"].tolist() == [10, 20, 30]

    def test_negative_integers(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["delta"],
            rows=[{"delta": "-5"}, {"delta": "10"}, {"delta": "-3"}],
        )
        dataset = normalizer.normalize(raw)

        col = next(c for c in dataset.schema if c.name == "delta")
        assert col.dtype == DataType.INTEGER


class TestTypeInferenceFloat:
    def test_float_column(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["price"],
            rows=[{"price": "29.99"}, {"price": "49.99"}, {"price": "19.99"}],
        )
        dataset = normalizer.normalize(raw)

        col = next(c for c in dataset.schema if c.name == "price")
        assert col.dtype == DataType.FLOAT
        assert dataset.dataframe["price"].tolist() == [29.99, 49.99, 19.99]

    def test_mixed_int_and_float(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["value"],
            rows=[{"value": "10"}, {"value": "20.5"}, {"value": "30"}],
        )
        dataset = normalizer.normalize(raw)

        col = next(c for c in dataset.schema if c.name == "value")
        assert col.dtype == DataType.FLOAT


class TestTypeInferenceDate:
    def test_iso_date_column(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["date"],
            rows=[
                {"date": "2024-01-15"},
                {"date": "2024-03-01"},
                {"date": "2024-06-10"},
            ],
        )
        dataset = normalizer.normalize(raw)

        col = next(c for c in dataset.schema if c.name == "date")
        assert col.dtype == DataType.DATE

    def test_us_date_format(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["date"],
            rows=[{"date": "01/15/2024"}, {"date": "03/01/2024"}],
        )
        dataset = normalizer.normalize(raw)

        col = next(c for c in dataset.schema if c.name == "date")
        assert col.dtype == DataType.DATE


class TestTypeInferenceBoolean:
    def test_boolean_column(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["active"],
            rows=[{"active": "true"}, {"active": "false"}, {"active": "true"}],
        )
        dataset = normalizer.normalize(raw)

        col = next(c for c in dataset.schema if c.name == "active")
        assert col.dtype == DataType.BOOLEAN
        assert dataset.dataframe["active"].tolist() == [True, False, True]

    def test_yes_no_boolean(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["flag"],
            rows=[{"flag": "yes"}, {"flag": "no"}, {"flag": "yes"}],
        )
        dataset = normalizer.normalize(raw)

        col = next(c for c in dataset.schema if c.name == "flag")
        assert col.dtype == DataType.BOOLEAN


class TestTypeInferenceMixed:
    def test_mixed_falls_back_to_string(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["mixed"],
            rows=[{"mixed": "hello"}, {"mixed": "42"}, {"mixed": "world"}],
        )
        dataset = normalizer.normalize(raw)

        col = next(c for c in dataset.schema if c.name == "mixed")
        assert col.dtype == DataType.STRING


# ---- Null Handling ----


class TestNullHandling:
    def test_empty_string_is_null(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["value"],
            rows=[{"value": "10"}, {"value": ""}, {"value": "30"}],
        )
        dataset = normalizer.normalize(raw)

        assert dataset.dataframe["value"].tolist()[0] == 10
        assert dataset.dataframe["value"].isna().tolist()[1] is True
        assert dataset.dataframe["value"].tolist()[2] == 30

    def test_null_string_is_null(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["name"],
            rows=[{"name": "Alice"}, {"name": "null"}, {"name": "Bob"}],
        )
        dataset = normalizer.normalize(raw)

        values = dataset.dataframe["name"]
        assert values.iloc[0] == "Alice"
        assert bool(values.isna().iloc[1])
        assert values.iloc[2] == "Bob"

    def test_na_string_is_null(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["score"],
            rows=[{"score": "100"}, {"score": "N/A"}, {"score": "85"}],
        )
        dataset = normalizer.normalize(raw)

        assert dataset.dataframe["score"].isna().tolist()[1] is True

    def test_none_value_is_null(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["val"],
            rows=[{"val": "10"}, {"val": None}, {"val": "30"}],
        )
        dataset = normalizer.normalize(raw)

        col = next(c for c in dataset.schema if c.name == "val")
        assert col.nullable is True


# ---- Schema Generation ----


class TestSchemaGeneration:
    def test_correct_schema(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["name", "age", "salary", "active"],
            rows=[
                {"name": "Alice", "age": "30", "salary": "75000.50", "active": "true"},
                {"name": "Bob", "age": "25", "salary": "62000.00", "active": "false"},
            ],
        )
        dataset = normalizer.normalize(raw)

        schema_map = {c.name: c.dtype for c in dataset.schema}
        assert schema_map["name"] == DataType.STRING
        assert schema_map["age"] == DataType.INTEGER
        assert schema_map["salary"] == DataType.FLOAT
        assert schema_map["active"] == DataType.BOOLEAN

    def test_nullable_flagged_correctly(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["required", "optional"],
            rows=[
                {"required": "yes", "optional": "A"},
                {"required": "no", "optional": ""},
            ],
        )
        dataset = normalizer.normalize(raw)

        required_col = next(c for c in dataset.schema if c.name == "required")
        optional_col = next(c for c in dataset.schema if c.name == "optional")
        assert required_col.nullable is False
        assert optional_col.nullable is True


# ---- Provenance ----


class TestProvenanceTracking:
    def test_carries_source_info(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["x"],
            rows=[{"x": "1"}, {"x": "2"}],
            name="my_source",
        )
        dataset = normalizer.normalize(raw)

        assert dataset.provenance.source_type == "csv"
        assert dataset.provenance.source_name == "my_source"
        assert dataset.provenance.source_path == "/test/data.csv"
        assert dataset.provenance.row_count_raw == 2
        assert dataset.provenance.loaded_at is not None
        assert dataset.provenance.normalized_at is not None


# ---- Empty Data ----


class TestNormalizerEmptyData:
    def test_empty_rows(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(headers=["x", "y"], rows=[])
        dataset = normalizer.normalize(raw)

        assert dataset.row_count == 0
        assert len(dataset.schema) == 2

    def test_no_headers(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(headers=[], rows=[])
        dataset = normalizer.normalize(raw)

        assert dataset.row_count == 0
        assert dataset.schema == []

    def test_all_null_column(self):
        normalizer = TabularNormalizer()
        raw = _make_raw_data(
            headers=["empty"],
            rows=[{"empty": ""}, {"empty": "null"}, {"empty": None}],
        )
        dataset = normalizer.normalize(raw)

        col = next(c for c in dataset.schema if c.name == "empty")
        assert col.dtype == DataType.STRING
        assert col.nullable is True
