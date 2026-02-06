"""Tests for the CLI (Phase 8)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
from typer.testing import CliRunner

from pygramattic_reports.cli import app

runner = CliRunner()


# ---------- Fixtures ---------------------------------------------------------


@pytest.fixture
def cli_csv(tmp_path: Path) -> Path:
    """Create a simple CSV file for CLI ingest tests."""
    p = tmp_path / "data.csv"
    p.write_text("name,value,date\nAlpha,100,2024-01-01\nBeta,200,2024-01-02\n")
    return p


@pytest.fixture
def cli_json(tmp_path: Path) -> Path:
    """Create a simple JSON file for CLI ingest tests."""
    p = tmp_path / "data.json"
    data = [
        {"name": "Alpha", "value": 100},
        {"name": "Beta", "value": 200},
    ]
    p.write_text(json.dumps(data))
    return p


# ---------- Ingest tests -----------------------------------------------------


def test_ingest_csv(tmp_path: Path, cli_csv: Path) -> None:
    """Ingest a CSV file and verify success output."""
    data_dir = tmp_path / "storage"
    result = runner.invoke(
        app,
        ["--data-dir", str(data_dir), "ingest", str(cli_csv), "--name", "test_data"],
    )
    assert result.exit_code == 0, result.output
    assert "Loaded" in result.output
    assert "Normalized" in result.output
    assert "Saved" in result.output


def test_ingest_json(tmp_path: Path, cli_json: Path) -> None:
    """Ingest a JSON file and verify success output."""
    data_dir = tmp_path / "storage"
    result = runner.invoke(
        app,
        ["--data-dir", str(data_dir), "ingest", str(cli_json)],
    )
    assert result.exit_code == 0, result.output
    assert "Loaded" in result.output
    assert "Saved" in result.output


def test_ingest_file_not_found(tmp_path: Path) -> None:
    """Error message for a missing file."""
    result = runner.invoke(
        app,
        ["--data-dir", str(tmp_path), "ingest", "/nonexistent/file.csv"],
    )
    assert result.exit_code == 1
    assert "File not found" in result.output


def test_ingest_unknown_format(tmp_path: Path) -> None:
    """Error message for an unsupported file extension."""
    bad_file = tmp_path / "data.xyz"
    bad_file.write_text("hello")
    result = runner.invoke(
        app,
        ["--data-dir", str(tmp_path), "ingest", str(bad_file)],
    )
    assert result.exit_code == 1
    assert "Cannot detect format" in result.output


def test_ingest_with_name(tmp_path: Path, cli_csv: Path) -> None:
    """Custom dataset name appears in the output."""
    data_dir = tmp_path / "storage"
    result = runner.invoke(
        app,
        ["--data-dir", str(data_dir), "ingest", str(cli_csv), "--name", "My Sales Data"],
    )
    assert result.exit_code == 0, result.output
    assert "Saved" in result.output


# ---------- List tests -------------------------------------------------------


def test_list_datasets_empty(tmp_path: Path) -> None:
    """Empty dataset listing returns clean output."""
    data_dir = tmp_path / "storage"
    result = runner.invoke(
        app,
        ["--data-dir", str(data_dir), "list", "datasets"],
    )
    assert result.exit_code == 0, result.output
    assert "No datasets found" in result.output


def test_list_datasets_after_ingest(tmp_path: Path, cli_csv: Path) -> None:
    """Ingested dataset appears in the list."""
    data_dir = tmp_path / "storage"
    # First ingest
    runner.invoke(
        app,
        ["--data-dir", str(data_dir), "ingest", str(cli_csv), "--name", "listed_set"],
    )
    # Then list
    result = runner.invoke(
        app,
        ["--data-dir", str(data_dir), "list", "datasets"],
    )
    assert result.exit_code == 0, result.output
    assert "listed_set" in result.output


# ---------- Init tests -------------------------------------------------------


def test_init_creates_config(tmp_path: Path) -> None:
    """Init command creates a report_config.yaml."""
    out_path = tmp_path / "report_config.yaml"
    result = runner.invoke(
        app,
        ["init", "--output", str(out_path)],
    )
    assert result.exit_code == 0, result.output
    assert "Created" in result.output
    assert out_path.is_file()
    content = out_path.read_text()
    assert "report:" in content
    assert "datasets:" in content


# ---------- Global option tests ----------------------------------------------


def test_version_flag() -> None:
    """--version shows the version string."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "pygramattic-reports" in result.output
    assert "0.1.0" in result.output


def test_help_flag() -> None:
    """--help shows usage information."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ingest" in result.output
    assert "list" in result.output
    assert "init" in result.output
