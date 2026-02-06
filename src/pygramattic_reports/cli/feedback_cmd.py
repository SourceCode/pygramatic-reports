"""Feedback command for the CLI.

Compares original and edited report files and produces
improvement recommendations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console

from pygramattic_reports.config import load_config
from pygramattic_reports.config.settings import StorageConfig
from pygramattic_reports.feedback import FeedbackAnalyzer, ReportDiffer

if TYPE_CHECKING:
    from pygramattic_reports.ai import ClaudeClient
    from pygramattic_reports.config import AppConfig

console = Console()


def feedback(
    ctx: typer.Context,
    original: str = typer.Argument(
        ...,
        help="Path to the original generated report",
    ),
    edited: str = typer.Argument(
        ...,
        help="Path to the user-edited version",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Save feedback report to file (JSON)",
    ),
) -> None:
    """Analyze changes between original and edited reports.

    Compares two report files and produces recommendations for
    improving future report generation.
    """
    quiet = ctx.obj.get("quiet", False) if ctx.obj else False
    original_path = Path(original)
    edited_path = Path(edited)

    differ = ReportDiffer()
    try:
        diff = differ.compare(original_path, edited_path)
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from None

    app_config = _load_app_config(ctx)
    claude_client = _try_claude_client(app_config)

    analyzer = FeedbackAnalyzer(client=claude_client)
    report = analyzer.analyze(diff)

    if not quiet:
        _print_feedback(diff, report)

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_data = {
            "original": diff.original_path,
            "edited": diff.edited_path,
            "format": diff.format,
            "total_changes": diff.total_changes,
            "summary": diff.summary,
            "recommendations": [
                {
                    "category": r.category,
                    "section": r.section,
                    "description": r.description,
                    "priority": r.priority,
                }
                for r in report.recommendations
            ],
            "ai_analysis": report.ai_analysis,
        }
        out_path.write_text(
            json.dumps(out_data, indent=2),
            encoding="utf-8",
        )
        if not quiet:
            console.print(f"\n[green]\u2713[/green] Saved to {out_path}")


# -- Internal helpers ---------------------------------------------------------


def _load_app_config(ctx: typer.Context) -> AppConfig:
    """Build AppConfig from CLI context."""
    obj: dict[str, object] = ctx.obj or {}
    config_path = obj.get("config_path")
    data_dir = obj.get("data_dir")
    overrides: dict[str, object] = {}
    if data_dir is not None:
        overrides["storage"] = StorageConfig(data_dir=data_dir)
    config_dir = config_path.parent if isinstance(config_path, Path) else None
    return load_config(config_dir=config_dir, overrides=overrides)


def _try_claude_client(app_config: AppConfig) -> ClaudeClient | None:
    """Try to create a Claude client."""
    from pygramattic_reports.ai import ClaudeClient  # noqa: PLC0415

    client = ClaudeClient(app_config.claude)
    if client.is_available():
        return client
    return None


def _print_feedback(diff: object, report: object) -> None:
    """Print feedback results to the console."""
    from pygramattic_reports.feedback import FeedbackReport, ReportDiff  # noqa: PLC0415

    if not isinstance(diff, ReportDiff) or not isinstance(report, FeedbackReport):
        return

    console.print(f"\nComparing: {diff.original_path} \u2192 {diff.edited_path}")
    console.print(f"  Format: {diff.format}")
    console.print(f"  Changes: {diff.summary}")

    if report.recommendations:
        console.print("\nRecommendations:")
        for i, rec in enumerate(report.recommendations, 1):
            console.print(f"  {i}. [{rec.category.title()}] {rec.section}")
            console.print(f"     {rec.description}")
    else:
        console.print("\nNo recommendations.")
