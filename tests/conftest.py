"""Shared test fixtures for pygramattic-reports."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory structure matching production layout."""
    for subdir in ("raw", "processed", "derived", "reports", "media"):
        (tmp_path / subdir).mkdir()
    return tmp_path


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    """Create a sample CSV file for testing."""
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(
        "name,value,date\nAlpha,100,2024-01-01\nBeta,200,2024-01-02\nGamma,150,2024-01-03\n"
    )
    return csv_path


@pytest.fixture
def sample_json(tmp_path: Path) -> Path:
    """Create a sample JSON file for testing."""
    json_path = tmp_path / "sample.json"
    data = [
        {"name": "Alpha", "value": 100, "date": "2024-01-01"},
        {"name": "Beta", "value": 200, "date": "2024-01-02"},
        {"name": "Gamma", "value": 150, "date": "2024-01-03"},
    ]
    json_path.write_text(json.dumps(data, indent=2))
    return json_path
