"""Integration tests for CLI build and export commands (Phase 16).

These tests exercise the full pipeline: ingest → build → verify output.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import yaml
from typer.testing import CliRunner

from pygramattic_reports.cli import app

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


# ---------- Helpers ----------------------------------------------------------


def _ingest_csv(tmp_path: Path) -> tuple[Path, str]:
    """Ingest the fixture CSV and return (data_dir, dataset_id).

    Creates a minimal CSV, ingests it, and extracts the dataset ID
    from the CLI output.
    """
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text("region,revenue,cost\nUS,1500,800\nEU,2300,1100\nAPAC,890,500\n")
    data_dir = tmp_path / "storage"
    result = runner.invoke(
        app,
        ["--data-dir", str(data_dir), "ingest", str(csv_path), "--name", "sales"],
    )
    assert result.exit_code == 0, result.output
    # Extract dataset ID from the structlog "Saved dataset" line
    for line in result.output.splitlines():
        if "dataset_id=" in line:
            for part in line.split():
                if part.startswith("dataset_id="):
                    return data_dir, part.split("=", 1)[1]
    msg = f"Could not extract dataset ID from output:\n{result.output}"
    raise AssertionError(msg)


def _write_report_config(
    tmp_path: Path,
    dataset_id: str,
    formats: list[str] | None = None,
    template: str = "default",
    theme: str = "default",
) -> Path:
    """Write a report_config.yaml for testing."""
    config = {
        "report_name": "Test Sales Report",
        "template": template,
        "theme": theme,
        "datasets": {"main": dataset_id},
        "primary_dataset": "main",
        "output_formats": formats or ["md"],
        "ai_enabled": False,
    }
    config_path = tmp_path / "report_config.yaml"
    config_path.write_text(yaml.dump(config))
    return config_path


# ---------- Build: Markdown --------------------------------------------------


class TestBuildMarkdownReport:
    """Full pipeline: ingest CSV → build → verify .md output."""

    def test_build_markdown_report(self, tmp_path: Path) -> None:
        data_dir, ds_id = _ingest_csv(tmp_path)
        config_path = _write_report_config(tmp_path, ds_id)

        result = runner.invoke(
            app,
            [
                "--data-dir",
                str(data_dir),
                "build",
                str(config_path),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Built" in result.output
        assert "report.md" in result.output
        assert "build_log.json" in result.output


# ---------- Build: DOCX ------------------------------------------------------


class TestBuildDocxReport:
    """Full pipeline producing DOCX."""

    def test_build_docx_report(self, tmp_path: Path) -> None:
        data_dir, ds_id = _ingest_csv(tmp_path)
        config_path = _write_report_config(tmp_path, ds_id, formats=["docx"])

        result = runner.invoke(
            app,
            [
                "--data-dir",
                str(data_dir),
                "build",
                str(config_path),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "report.docx" in result.output


# ---------- Build: Multiple formats ------------------------------------------


class TestBuildMultipleFormats:
    """Build with -o md -o docx produces both files."""

    def test_build_multiple_formats(self, tmp_path: Path) -> None:
        data_dir, ds_id = _ingest_csv(tmp_path)
        config_path = _write_report_config(tmp_path, ds_id)

        result = runner.invoke(
            app,
            [
                "--data-dir",
                str(data_dir),
                "build",
                str(config_path),
                "-o",
                "md",
                "-o",
                "docx",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "report.md" in result.output
        assert "report.docx" in result.output


# ---------- Build: Missing config --------------------------------------------


class TestBuildMissingConfig:
    """Proper error for missing config file."""

    def test_build_missing_config(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "--data-dir",
                str(tmp_path),
                "build",
                str(tmp_path / "nonexistent.yaml"),
            ],
        )
        assert result.exit_code == 1
        assert "not found" in result.output


# ---------- Build: Missing dataset -------------------------------------------


class TestBuildMissingDataset:
    """Proper error for referenced dataset not found."""

    def test_build_missing_dataset(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "storage"
        config_path = _write_report_config(tmp_path, "nonexistent_id")

        result = runner.invoke(
            app,
            [
                "--data-dir",
                str(data_dir),
                "build",
                str(config_path),
            ],
        )
        assert result.exit_code == 1
        assert "Error" in result.output


# ---------- Build: Dry run ---------------------------------------------------


class TestBuildDryRun:
    """Dry run shows plan but writes no files."""

    def test_build_dry_run(self, tmp_path: Path) -> None:
        data_dir, ds_id = _ingest_csv(tmp_path)
        config_path = _write_report_config(tmp_path, ds_id)

        result = runner.invoke(
            app,
            [
                "--data-dir",
                str(data_dir),
                "build",
                str(config_path),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Dry run" in result.output
        # No report files should have been written
        assert "report.md" not in result.output


# ---------- Build: Template override -----------------------------------------


class TestBuildTemplateOverride:
    """--template flag works."""

    def test_build_with_template_override(self, tmp_path: Path) -> None:
        data_dir, ds_id = _ingest_csv(tmp_path)
        # quarterly_report template expects dataset named "main_data"
        config_path = _write_report_config(
            tmp_path,
            ds_id,
            template="default",
        )
        # Rewrite config with main_data key for quarterly template
        config = {
            "report_name": "Test Sales Report",
            "template": "default",
            "theme": "default",
            "datasets": {"main_data": ds_id},
            "primary_dataset": "main_data",
            "output_formats": ["md"],
            "ai_enabled": False,
        }
        config_path.write_text(yaml.dump(config))

        result = runner.invoke(
            app,
            [
                "--data-dir",
                str(data_dir),
                "build",
                str(config_path),
                "--template",
                "quarterly_report",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "quarterly_report" in result.output


# ---------- Export: JSON -----------------------------------------------------


class TestExportJson:
    """Export dataset to JSON."""

    def test_export_json(self, tmp_path: Path) -> None:
        data_dir, ds_id = _ingest_csv(tmp_path)
        out_file = tmp_path / "export.json"

        result = runner.invoke(
            app,
            [
                "--data-dir",
                str(data_dir),
                "export",
                ds_id,
                "-f",
                "json",
                "-o",
                str(out_file),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert len(data) == 3
        assert data[0]["region"] == "US"


# ---------- Export: CSV ------------------------------------------------------


class TestExportCsv:
    """Export dataset to CSV."""

    def test_export_csv(self, tmp_path: Path) -> None:
        data_dir, ds_id = _ingest_csv(tmp_path)
        out_file = tmp_path / "export.csv"

        result = runner.invoke(
            app,
            [
                "--data-dir",
                str(data_dir),
                "export",
                ds_id,
                "-f",
                "csv",
                "-o",
                str(out_file),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out_file.exists()
        content = out_file.read_text()
        assert "region" in content
        assert "US" in content


# ---------- Export: SQL ------------------------------------------------------


class TestExportSql:
    """Export dataset to SQL."""

    def test_export_sql(self, tmp_path: Path) -> None:
        data_dir, ds_id = _ingest_csv(tmp_path)
        out_file = tmp_path / "export.sql"

        result = runner.invoke(
            app,
            [
                "--data-dir",
                str(data_dir),
                "export",
                ds_id,
                "-f",
                "sql",
                "-o",
                str(out_file),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out_file.exists()
        content = out_file.read_text()
        assert "CREATE TABLE" in content
        assert "INSERT INTO" in content


# ---------- Export: Missing dataset ------------------------------------------


class TestExportMissingDataset:
    """Proper error for missing dataset."""

    def test_export_missing_dataset(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "storage"
        result = runner.invoke(
            app,
            [
                "--data-dir",
                str(data_dir),
                "export",
                "nonexistent_id",
                "-f",
                "json",
                "-o",
                str(tmp_path / "out.json"),
            ],
        )
        assert result.exit_code == 1
        assert "Error" in result.output
