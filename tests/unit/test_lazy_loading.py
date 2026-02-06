"""Tests for Lazy Loading functionality."""

from __future__ import annotations

from unittest.mock import Mock

import pandas as pd

from pygramattic_reports.core.lazy import LazyDataset
from pygramattic_reports.models import ColumnSchema, DataType, Provenance, SourceType, now_utc


class TestLazyDataset:
    """Tests for the LazyDataset class."""

    def test_lazy_initialization(self):
        """Test that data is NOT loaded upon initialization."""
        loader_mock = Mock()

        dataset = LazyDataset(id="lazy_test", name="Lazy Test", loader=loader_mock)

        # Verify basic properties work without loading
        assert dataset.id == "lazy_test"
        assert dataset.name == "Lazy Test"
        assert dataset.created_at is not None

        # Verify loader was NOT called
        loader_mock.assert_not_called()

    def test_lazy_access_triggers_load(self):
        """Test that accessing dataframe triggers the loader exactly once."""
        # Setup mock return values
        df = pd.DataFrame({"col1": [1, 2, 3]})
        schema = [ColumnSchema(name="col1", dtype=DataType.INTEGER)]
        provenance = Provenance(
            source_type=SourceType.CSV,
            source_name="test_source",
            loaded_at=now_utc(),
            normalized_at=now_utc(),
            row_count_raw=3,
        )

        loader_mock = Mock(return_value=(df, schema, provenance))

        dataset = LazyDataset(id="lazy_test", name="Lazy Test", loader=loader_mock)

        # Access dataframe
        result_df = dataset.dataframe

        # Verify loader called ONCE
        loader_mock.assert_called_once()

        # Verify data correctness
        pd.testing.assert_frame_equal(result_df, df)

        # Access again - loader should NOT be called again
        _ = dataset.dataframe
        loader_mock.assert_called_once()

    def test_schema_access_triggers_load(self):
        """Test that accessing schema triggers the loader."""
        df = pd.DataFrame({"col1": [1]})
        schema = [ColumnSchema(name="col1", dtype=DataType.INTEGER)]
        provenance = Provenance(
            source_type=SourceType.CSV,
            source_name="test",
            loaded_at=now_utc(),
            normalized_at=now_utc(),
            row_count_raw=1,
        )
        loader_mock = Mock(return_value=(df, schema, provenance))

        dataset = LazyDataset("id", "name", loader_mock)

        # Access schema
        res_schema = dataset.schema

        loader_mock.assert_called_once()
        assert res_schema == schema

    def test_inherited_properties_work(self):
        """Test that row_count and column_names (from base class) trigger load."""
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        schema = [
            ColumnSchema(name="col1", dtype=DataType.INTEGER),
            ColumnSchema(name="col2", dtype=DataType.STRING),
        ]
        provenance = Provenance(
            source_type=SourceType.CSV,
            source_name="test",
            loaded_at=now_utc(),
            normalized_at=now_utc(),
            row_count_raw=2,
        )
        loader_mock = Mock(return_value=(df, schema, provenance))

        dataset = LazyDataset("id", "name", loader_mock)

        # Access inherited property row_count
        # This calls self.dataframe under the hood in base class
        assert dataset.row_count == 2

        loader_mock.assert_called_once()

        # Access inherited property column_names
        # This calls self.schema under the hood
        assert dataset.column_names == ["col1", "col2"]

        # Should still be 1 call (memoized)
        loader_mock.assert_called_once()
