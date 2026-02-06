"""Integration tests for validate and feedback CLI commands (Phase 20)."""

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
    """Ingest fixture CSV and return (data_dir, dataset_id)."""
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text("region,revenue,cost\nUS,1500,800\nEU,2300,1100\nAPAC,890,500\n")
    data_dir = tmp_path / "storage"
    result = runner.invoke(
        app,
        ["--data-dir", str(data_dir), "ingest", str(csv_path), "--name", "sales"],
    )
    assert result.exit_code == 0, result.output
    for line in result.output.splitlines():
        if "dataset_id=" in line:
            for part in line.split():
                if part.startswith("dataset_id="):
                    return data_dir, part.split("=", 1)[1]
    msg = f"Could not extract dataset ID from output:\n{result.output}"
    raise AssertionError(msg)


def _build_report(
    tmp_path: Path,
    data_dir: Path,
    ds_id: str,
    formats: list[str] | None = None,
) -> str:
    """Build a report and return the report ID from output."""
    config = {
        "report_name": "Test Sales Report",
        "template": "default",
        "theme": "default",
        "datasets": {"main": ds_id},
        "primary_dataset": "main",
        "output_formats": formats or ["md"],
        "ai_enabled": False,
    }
    config_path = tmp_path / "report_config.yaml"
    config_path.write_text(yaml.dump(config))

    result = runner.invoke(
        app,
        ["--data-dir", str(data_dir), "build", str(config_path)],
    )
    assert result.exit_code == 0, result.output
    return result.output


# ---------- Feedback: full workflow ------------------------------------------


class TestFeedbackProducesRecommendations:
    """Full feedback workflow: create files, compare, get recommendations."""

    def test_feedback_produces_recommendations(self, tmp_path: Path) -> None:
        orig = tmp_path / "report.md"
        edited = tmp_path / "report_edited.md"
        orig.write_text("# Sales Report\n\nDetailed analysis of quarterly revenue.\n")
        edited.write_text("# Sales Report\n\nBrief summary.\n\nNew section added.\n")

        result = runner.invoke(
            app,
            ["feedback", str(orig), str(edited)],
        )
        assert result.exit_code == 0, result.output
        assert "Comparing" in result.output
        assert "Recommendations" in result.output or "No recommendations" in result.output

    def test_feedback_json_output(self, tmp_path: Path) -> None:
        orig = tmp_path / "report.md"
        edited = tmp_path / "report_edited.md"
        orig.write_text("# Title\n\nOriginal content paragraph.\n")
        edited.write_text("# Title\n\nEdited.\n")

        out_json = tmp_path / "feedback.json"
        result = runner.invoke(
            app,
            [
                "feedback",
                str(orig),
                str(edited),
                "--output",
                str(out_json),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out_json.exists()

        data = json.loads(out_json.read_text())
        assert "total_changes" in data
        assert "recommendations" in data

    def test_feedback_no_changes(self, tmp_path: Path) -> None:
        report = tmp_path / "report.md"
        report.write_text("# Title\n\nContent.\n")
        copy = tmp_path / "report_copy.md"
        copy.write_text("# Title\n\nContent.\n")

        result = runner.invoke(
            app,
            ["feedback", str(report), str(copy)],
        )
        assert result.exit_code == 0, result.output
        assert "No changes" in result.output

    def test_feedback_missing_file(self, tmp_path: Path) -> None:
        orig = tmp_path / "report.md"
        orig.write_text("content")

        result = runner.invoke(
            app,
            ["feedback", str(orig), str(tmp_path / "missing.md")],
        )
        assert result.exit_code == 1
        assert "Error" in result.output
