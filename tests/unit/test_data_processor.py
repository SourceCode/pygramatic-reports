from datetime import UTC, datetime

import pandas as pd
import pytest

from pygramattic_reports.models import (
    ColumnSchema,
    Dataset,
    DataType,
    Provenance,
    TemplateSectionSpec,
)
from pygramattic_reports.processors.data_processor import DataProcessor


@pytest.fixture
def sample_dataset():
    data = {
        "id": [1, 2, 3, 4, 5],
        "category": ["A", "A", "B", "B", "C"],
        "value": [10.0, 20.0, 30.0, 40.0, 50.0],
        "date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"],
    }
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])

    schema = [
        ColumnSchema(name="id", dtype=DataType.INTEGER),
        ColumnSchema(name="category", dtype=DataType.STRING),
        ColumnSchema(name="value", dtype=DataType.FLOAT),
        ColumnSchema(name="date", dtype=DataType.DATETIME),
    ]

    provenance = Provenance(
        source_type="test",
        source_name="test_data",
        loaded_at=datetime.now(UTC),
        normalized_at=datetime.now(UTC),
        row_count_raw=5,
    )

    return Dataset(
        id="test_ds", name="Test Dataset", schema=schema, dataframe=df, provenance=provenance
    )


def test_filtering(sample_dataset):
    spec = TemplateSectionSpec(
        type="data_table", filters=[{"col": "category", "op": "eq", "val": "A"}]
    )
    processor = DataProcessor()
    df = processor.process(sample_dataset, spec)
    assert len(df) == 2
    assert all(df["category"] == "A")


def test_filtering_numeric(sample_dataset):
    spec = TemplateSectionSpec(
        type="data_table", filters=[{"col": "value", "op": "gt", "val": 30.0}]
    )
    processor = DataProcessor()
    df = processor.process(sample_dataset, spec)
    assert len(df) == 2
    assert all(df["value"] > 30.0)


def test_sorting(sample_dataset):
    spec = TemplateSectionSpec(type="data_table", sort=["-value"])
    processor = DataProcessor()
    df = processor.process(sample_dataset, spec)
    assert df.iloc[0]["value"] == 50.0
    assert df.iloc[-1]["value"] == 10.0


def test_limit(sample_dataset):
    spec = TemplateSectionSpec(type="data_table", limit=2)
    processor = DataProcessor()
    df = processor.process(sample_dataset, spec)
    assert len(df) == 2


def test_calculated_columns(sample_dataset):
    spec = TemplateSectionSpec(type="data_table", calculated_columns={"double_val": "value * 2"})
    processor = DataProcessor()
    df = processor.process(sample_dataset, spec)
    assert "double_val" in df.columns
    assert df.iloc[0]["double_val"] == 20.0


def test_grouping_aggregation(sample_dataset):
    spec = TemplateSectionSpec(
        type="data_table", group_by=["category"], aggregations={"value": "sum"}
    )
    processor = DataProcessor()
    df = processor.process(sample_dataset, spec)

    assert len(df) == 3  # A, B, C
    row_a = df[df["category"] == "A"].iloc[0]
    assert row_a["value"] == 30.0  # 10 + 20
    row_b = df[df["category"] == "B"].iloc[0]
    assert row_b["value"] == 70.0  # 30 + 40
