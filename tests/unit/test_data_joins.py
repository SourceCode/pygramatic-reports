"""Tests for DataProcessor join functionality."""

from unittest.mock import Mock

import pandas as pd

from pygramattic_reports.models import Dataset, Provenance, TemplateSectionSpec, now_utc
from pygramattic_reports.processors.data_processor import DataProcessor


def make_dataset(id: str, data: dict) -> Dataset:
    return Dataset(
        id=id,
        name=id,
        dataframe=pd.DataFrame(data),
        schema=[],  # Schema not strictly needed for this test
        provenance=Mock(spec=Provenance),
        created_at=now_utc(),
    )


class TestDataJoins:
    def test_basic_left_join(self):
        """Test a simple left join between two datasets."""
        # Primary: Orders
        ds_orders = make_dataset(
            "orders",
            {"order_id": [1, 2, 3], "customer_id": [101, 102, 103], "amount": [100, 200, 300]},
        )

        # Secondary: Customers
        ds_customers = make_dataset(
            "customers", {"customer_id": [101, 102], "name": ["Alice", "Bob"]}
        )

        processor = DataProcessor()
        spec = TemplateSectionSpec(
            type="data_table", joins=[{"dataset": "customers", "on": "customer_id", "how": "left"}]
        )

        result = processor.process(
            ds_orders, spec, other_datasets={"customers": ds_customers, "orders": ds_orders}
        )

        assert len(result) == 3
        assert "name" in result.columns
        # row 1 (101) -> Alice
        assert result.loc[result["order_id"] == 1, "name"].iloc[0] == "Alice"
        # row 3 (103) -> NaN (Customer not found)
        assert pd.isna(result.loc[result["order_id"] == 3, "name"].iloc[0])

    def test_inner_join_filtering(self):
        """Test that inner join filters rows."""
        ds_a = make_dataset("A", {"id": [1, 2, 3]})
        ds_b = make_dataset("B", {"id": [2, 3, 4]})

        processor = DataProcessor()
        spec = TemplateSectionSpec(
            type="data_table", joins=[{"dataset": "B", "on": "id", "how": "inner"}]
        )

        result = processor.process(ds_a, spec, {"B": ds_b})

        assert len(result) == 2
        assert sorted(result["id"].tolist()) == [2, 3]

    def test_custom_keys(self):
        """Test joining on different column names (left_on, right_on)."""
        ds_a = make_dataset("A", {"user_id": [1]})
        ds_b = make_dataset("B", {"id": [1], "email": ["test@example.com"]})

        processor = DataProcessor()
        spec = TemplateSectionSpec(
            type="data_table",
            joins=[{"dataset": "B", "left_on": "user_id", "right_on": "id", "how": "left"}],
        )

        result = processor.process(ds_a, spec, {"B": ds_b})

        assert result.iloc[0]["email"] == "test@example.com"
