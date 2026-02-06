"""End-to-end integration test (Phase 20).

Exercises the full pipeline: raw CSV → ingest → build → validate output.
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


class TestFullPipelineCsvToValidatedReport:
    """Full pipeline: CSV → ingest → build → verify artifacts."""

    def test_full_pipeline_csv_to_validated_report(
        self,
        tmp_path: Path,
    ) -> None:
        # 1. Create test CSV data
        csv_path = tmp_path / "sales.csv"
        csv_path.write_text(
            "region,revenue,cost,profit\nUS,1500,800,700\nEU,2300,1100,1200\nAPAC,890,500,390\n"
        )
        data_dir = tmp_path / "storage"

        # 2. Ingest
        ingest_result = runner.invoke(
            app,
            [
                "--data-dir",
                str(data_dir),
                "ingest",
                str(csv_path),
                "--name",
                "sales",
            ],
        )
        assert ingest_result.exit_code == 0, ingest_result.output

        ds_id = None
        for line in ingest_result.output.splitlines():
            if "dataset_id=" in line:
                for part in line.split():
                    if part.startswith("dataset_id="):
                        ds_id = part.split("=", 1)[1]
                        break
        assert ds_id is not None, f"Could not extract dataset ID:\n{ingest_result.output}"

        # 3. Build (md + docx)
        config = {
            "report_name": "E2E Sales Report",
            "template": "default",
            "theme": "default",
            "datasets": {"main": ds_id},
            "primary_dataset": "main",
            "output_formats": ["md", "docx"],
            "ai_enabled": False,
        }
        config_path = tmp_path / "report_config.yaml"
        config_path.write_text(yaml.dump(config))

        build_result = runner.invoke(
            app,
            [
                "--data-dir",
                str(data_dir),
                "build",
                str(config_path),
            ],
        )
        assert build_result.exit_code == 0, build_result.output
        assert "report.md" in build_result.output
        assert "report.docx" in build_result.output

        # 4. Verify artifacts on disk
        reports_dir = data_dir / "reports"
        assert reports_dir.exists(), "reports directory missing"

        # Find the report subdirectory
        report_dirs = [d for d in reports_dir.iterdir() if d.is_dir()]
        assert len(report_dirs) >= 1, "No report directory found"

        report_dir = report_dirs[0]

        # Markdown file exists and contains expected content
        md_files = list(report_dir.glob("*.md"))
        assert len(md_files) >= 1, "No markdown file found"
        md_content = md_files[0].read_text(encoding="utf-8")
        assert "Sales" in md_content or "sales" in md_content

        # DOCX file exists and is non-empty
        docx_files = list(report_dir.glob("*.docx"))
        assert len(docx_files) >= 1, "No DOCX file found"
        assert docx_files[0].stat().st_size > 0

        # Build log exists and is valid JSON
        log_path = report_dir / "build_log.json"
        assert log_path.exists(), "build_log.json missing"
        build_log = json.loads(log_path.read_text(encoding="utf-8"))
        assert "build_id" in build_log
        assert "status" in build_log
