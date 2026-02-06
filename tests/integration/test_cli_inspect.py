"""Tests for Inspect CLI command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from pygramattic_reports.cli.main import app

runner = CliRunner()


@patch("pygramattic_reports.cli.inspect_cmd.Manifest")
@patch("pygramattic_reports.cli.inspect_cmd.Path")
def test_inspect_manifest(mock_path_cls, mock_manifest_cls, tmp_path):
    # Setup - mock data directory scanning
    mock_data_dir = MagicMock()
    mock_path_cls.return_value = mock_data_dir
    mock_data_dir.exists.return_value = True

    # Mock a manifest file
    mock_manifest_file = MagicMock()
    mock_manifest_file.read_text.return_value = "{}"
    mock_manifest_file.parent = Path("/data/ds1")

    mock_data_dir.glob.return_value = [mock_manifest_file]

    # Mock Manifest object
    mock_manifest = MagicMock()
    mock_manifest.id = "ds1"
    mock_manifest.name = "Test Dataset"
    mock_manifest.source_type = "csv"
    mock_manifest.row_count = 100

    mock_manifest_cls.model_validate_json.return_value = mock_manifest

    result = runner.invoke(app, ["inspect", "manifest"])

    assert result.exit_code == 0
    assert "Datasets in" in result.stdout
    assert "ds1" in result.stdout
    assert "Test Dataset" in result.stdout


@patch("pygramattic_reports.cli.inspect_cmd.Manifest")
@patch("pygramattic_reports.cli.inspect_cmd.Path")
@patch("pandas.read_parquet")
def test_inspect_dataset_parquet(mock_read_parquet, mock_path_cls, mock_manifest_cls, tmp_path):
    # Setup
    mock_data_dir = MagicMock()
    mock_path_cls.return_value = mock_data_dir
    mock_data_dir.exists.return_value = True

    mock_manifest_file = MagicMock()
    mock_manifest_file.read_text.return_value = "{}"
    mock_manifest_file.parent = MagicMock()  # Should be a path-like object that supports / operator

    mock_data_dir.glob.return_value = [mock_manifest_file]

    mock_manifest = MagicMock()
    mock_manifest.id = "ds1"
    mock_manifest.name = "Test Dataset"
    mock_manifest.source_type = "csv"
    mock_manifest.storage_path = "data.parquet"
    mock_manifest.format = "parquet"
    mock_manifest.created_at = "2023-01-01"

    col = MagicMock()
    col.name = "A"
    col.type = "NUMBER"
    mock_manifest.columns = [col]

    mock_manifest_cls.model_validate_json.return_value = mock_manifest

    # Mock DataFrame
    mock_df = MagicMock()
    mock_df.head.return_value = mock_df
    mock_df.columns = ["A"]
    mock_df.iterrows.return_value = []
    mock_read_parquet.return_value = mock_df

    # Fix the path join in inspect_dataset: manifest_file.parent / found_manifest.storage_path
    # mock_manifest_file.parent returns a MagicMock, joining it returns another MagicMock
    # which we need to make exists() return True
    mock_data_path = mock_manifest_file.parent.__truediv__.return_value
    mock_data_path.exists.return_value = True

    result = runner.invoke(app, ["inspect", "dataset", "ds1"])

    assert result.exit_code == 0
    assert "Dataset Inspector: ds1" in result.stdout
    assert "Schema" in result.stdout
