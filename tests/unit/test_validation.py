"""Tests for DataProcessor validation functionality."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from pygramattic_reports.exceptions import DataError
from pygramattic_reports.models import Dataset, Provenance, TemplateSectionSpec, now_utc
from pygramattic_reports.processors.data_processor import DataProcessor


def make_dataset(data: dict) -> Dataset:
    return Dataset(
        id="test",
        name="test",
        dataframe=pd.DataFrame(data),
        schema=[],
        provenance=Mock(spec=Provenance),
        created_at=now_utc(),
    )


class TestDataValidation:
    def test_completeness_warning(self):
        """Test that missing values trigger a warning."""
        ds = make_dataset({"val": [1, None, 3]})
        processor = DataProcessor()

        spec = TemplateSectionSpec(
            type="data_table",
            validation_rules=[{"type": "completeness", "col": "val", "level": "warning"}],
        )

        with patch("pygramattic_reports.processors.data_processor._logger") as mock_logger:
            processor.process(ds, spec)
            mock_logger.warning.assert_called()
            call_args = mock_logger.warning.call_args[1]
            assert "missing values" in call_args["message"]

    def test_completeness_error(self):
        """Test that missing values trigger an error if level is error."""
        ds = make_dataset({"val": [1, None, 3]})
        processor = DataProcessor()

        spec = TemplateSectionSpec(
            type="data_table",
            validation_rules=[{"type": "completeness", "col": "val", "level": "error"}],
        )

        with pytest.raises(DataError, match="missing values"):
            processor.process(ds, spec)

    def test_unique_rule(self):
        """Test uniqueness rule."""
        ds = make_dataset({"id": [1, 2, 2, 3]})
        processor = DataProcessor()
        spec = TemplateSectionSpec(
            type="data_table", validation_rules=[{"type": "unique", "col": "id", "level": "error"}]
        )

        with pytest.raises(DataError, match="duplicate values"):
            processor.process(ds, spec)

    def test_range_rule(self):
        """Test range rule."""
        ds = make_dataset({"score": [10, 50, 150]})
        processor = DataProcessor()
        spec = TemplateSectionSpec(
            type="data_table",
            validation_rules=[
                {"type": "range", "col": "score", "min": 0, "max": 100, "level": "error"}
            ],
        )

        with pytest.raises(DataError, match="outside range"):
            processor.process(ds, spec)
