"""Tests for the data processors (Phase 13)."""

from __future__ import annotations

import pandas as pd
import pytest

from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.models.dataset import ColumnSchema, Dataset, DataType, Provenance
from pygramattic_reports.processors import (
    aggregate,
    filter_rows,
    moving_average,
    percent_change,
    ratio,
    running_total,
)

# ---------- Helpers ----------------------------------------------------------


def _make_dataset(
    data: dict[str, list[object]],
    schema: list[ColumnSchema],
) -> Dataset:
    df = pd.DataFrame(data)
    return Dataset(
        id=generate_id(),
        name="test",
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


def _numeric_dataset() -> Dataset:
    return _make_dataset(
        data={
            "name": ["A", "B", "C", "D"],
            "value": [10, 20, 30, 40],
            "cost": [5, 10, 15, 20],
        },
        schema=[
            ColumnSchema(name="name", dtype=DataType.STRING),
            ColumnSchema(name="value", dtype=DataType.INTEGER),
            ColumnSchema(name="cost", dtype=DataType.INTEGER),
        ],
    )


# ---------- Aggregate tests --------------------------------------------------


class TestAggregateSum:
    """Test sum aggregation."""

    def test_aggregate_sum(self) -> None:
        ds = _numeric_dataset()
        assert aggregate(ds, "value", "sum") == 100.0


class TestAggregateAvg:
    """Test average aggregation."""

    def test_aggregate_avg(self) -> None:
        ds = _numeric_dataset()
        assert aggregate(ds, "value", "avg") == 25.0


class TestAggregateMinMax:
    """Test min and max aggregation."""

    def test_aggregate_min(self) -> None:
        ds = _numeric_dataset()
        assert aggregate(ds, "value", "min") == 10.0

    def test_aggregate_max(self) -> None:
        ds = _numeric_dataset()
        assert aggregate(ds, "value", "max") == 40.0

    def test_aggregate_count(self) -> None:
        ds = _numeric_dataset()
        assert aggregate(ds, "value", "count") == 4.0

    def test_aggregate_unknown_raises(self) -> None:
        ds = _numeric_dataset()
        with pytest.raises(ValueError, match="Unknown operation"):
            aggregate(ds, "value", "median")


# ---------- Filter tests -----------------------------------------------------


class TestFilterRowsEq:
    """Test equality filter."""

    def test_filter_rows_eq(self) -> None:
        ds = _numeric_dataset()
        result = filter_rows(ds, "name", "eq", "B")
        assert len(result) == 1
        assert result.iloc[0]["value"] == 20

    def test_filter_rows_gt(self) -> None:
        ds = _numeric_dataset()
        result = filter_rows(ds, "value", "gt", 20)
        assert len(result) == 2

    def test_filter_rows_contains(self) -> None:
        ds = _numeric_dataset()
        result = filter_rows(ds, "name", "contains", "A")
        assert len(result) == 1

    def test_filter_rows_unknown_raises(self) -> None:
        ds = _numeric_dataset()
        with pytest.raises(ValueError, match="Unknown operator"):
            filter_rows(ds, "name", "regex", ".*")


# ---------- Derived column tests ---------------------------------------------


class TestPercentChange:
    """Test percent change calculation."""

    def test_percent_change(self) -> None:
        ds = _numeric_dataset()
        result = percent_change(ds, "value")
        assert pd.isna(result.iloc[0])
        assert result.iloc[1] == pytest.approx(1.0)  # 10→20 = 100%
        assert result.iloc[2] == pytest.approx(0.5)  # 20→30 = 50%


class TestRatio:
    """Test column ratio."""

    def test_ratio(self) -> None:
        ds = _numeric_dataset()
        result = ratio(ds, "value", "cost")
        assert result.iloc[0] == pytest.approx(2.0)
        assert result.iloc[1] == pytest.approx(2.0)


class TestRunningTotal:
    """Test running total."""

    def test_running_total(self) -> None:
        ds = _numeric_dataset()
        result = running_total(ds, "value")
        assert list(result) == [10, 30, 60, 100]


class TestMovingAverage:
    """Test moving average."""

    def test_moving_average(self) -> None:
        ds = _numeric_dataset()
        result = moving_average(ds, "value", window=2)
        assert pd.isna(result.iloc[0])
        assert result.iloc[1] == pytest.approx(15.0)
        assert result.iloc[2] == pytest.approx(25.0)
        assert result.iloc[3] == pytest.approx(35.0)
