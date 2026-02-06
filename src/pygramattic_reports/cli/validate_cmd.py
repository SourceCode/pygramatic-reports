"""Validate command for the CLI.

Runs structural, numerical, and narrative validation checks
on a generated report.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console

from pygramattic_reports.config import load_config
from pygramattic_reports.config.settings import StorageConfig
from pygramattic_reports.logging import get_logger
from pygramattic_reports.models import CheckStatus
from pygramattic_reports.storage.manager import StorageManager
from pygramattic_reports.validator import ReportValidator

if TYPE_CHECKING:
    from pygramattic_reports.ai import ClaudeClient
    from pygramattic_reports.config import AppConfig

logger = get_logger("validate_cmd")


console = Console()


def validate(
    ctx: typer.Context,
    report_id: str = typer.Argument(
        ...,
        help="Report ID from storage",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Fail on warnings too",
    ),
    no_ai: bool = typer.Option(
        False,
        "--no-ai",
        help="Skip AI-assisted narrative validation",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Save validation report to file (JSON)",
    ),
) -> None:
    """Validate a generated report against source data.

    Runs structural, numerical, and optional AI-assisted narrative
    checks.  Prints results and optionally saves a JSON report.
    """
    quiet = ctx.obj.get("quiet", False) if ctx.obj else False
    app_config = _load_app_config(ctx)
    storage = StorageManager(app_config)
    storage.initialize()

    build_log_data = _load_build_log(storage, report_id)
    if build_log_data is None:
        console.print(f"[red]Error:[/red] Build log not found for {report_id}")
        raise typer.Exit(code=1)

    template, datasets = _load_build_artifacts(
        build_log_data,
        app_config,
        storage,
    )
    if template is None:
        console.print("[red]Error:[/red] Could not load template from build log")
        raise typer.Exit(code=1)

    report = _build_report_for_validation(
        build_log_data,
        app_config,
        storage,
    )
    if report is None:
        console.print("[red]Error:[/red] Could not rebuild report for validation")
        raise typer.Exit(code=1)

    claude_client = None if no_ai else _try_claude_client(app_config)

    validator = ReportValidator(claude_client=claude_client)
    result = validator.validate(report, template, datasets)  # type: ignore[arg-type]

    if not quiet:
        _print_results(result)

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(result.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )
        if not quiet:
            console.print(f"\n[green]\u2713[/green] Saved to {out_path}")

    if result.overall_status == CheckStatus.FAIL:
        raise typer.Exit(code=1)
    if strict and result.overall_status == CheckStatus.WARN:
        raise typer.Exit(code=1)


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


def _load_build_log(
    storage: StorageManager,
    report_id: str,
) -> dict[str, object] | None:
    """Try to load the build log for a report."""
    try:
        reports_dir = storage._resolve_stage_dir("reports") / report_id  # noqa: SLF001
        log_path = reports_dir / "build_log.json"
        if log_path.exists():
            return json.loads(log_path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
    except Exception:
        logger.debug("Failed to load build log for %s", report_id)
    return None


def _load_build_artifacts(
    build_log_data: dict[str, object],
    app_config: AppConfig,
    storage: StorageManager,
) -> tuple[object, dict[str, object]]:
    """Load template and datasets from a build log."""
    from pygramattic_reports.templates import TemplateLoader  # noqa: PLC0415

    template_name = build_log_data.get("template_name", "default")
    loader = TemplateLoader(templates_dir=app_config.templates_dir)
    try:
        template = loader.load(str(template_name))
    except Exception:
        return None, {}

    datasets: dict[str, object] = {}
    ds_ids = build_log_data.get("datasets_used", [])
    if isinstance(ds_ids, list):
        for ds_id in ds_ids:
            try:
                datasets[str(ds_id)] = storage.load_dataset(str(ds_id))
            except Exception:
                logger.debug("Failed to load dataset %s", ds_id)

    return template, datasets


def _build_report_for_validation(
    build_log_data: dict[str, object],
    app_config: AppConfig,
    storage: StorageManager,
) -> object | None:
    """Rebuild the report object for validation."""
    from pygramattic_reports.builder import ReportBuilder  # noqa: PLC0415
    from pygramattic_reports.charts import ChartEngine  # noqa: PLC0415
    from pygramattic_reports.templates import TemplateLoader, TemplateRenderer  # noqa: PLC0415
    from pygramattic_reports.themes import ThemeLoader  # noqa: PLC0415

    template_name = str(build_log_data.get("template_name", "default"))
    theme_name = str(build_log_data.get("theme_name", "default"))

    try:
        tpl_loader = TemplateLoader(templates_dir=app_config.templates_dir)
        template = tpl_loader.load(template_name)

        thm_loader = ThemeLoader(themes_dir=app_config.themes_dir)
        theme = thm_loader.load(theme_name)
    except Exception:
        return None

    datasets: dict[str, object] = {}
    ds_ids = build_log_data.get("datasets_used", [])
    if isinstance(ds_ids, list):
        for ds_id in ds_ids:
            try:
                ds = storage.load_dataset(str(ds_id))
                datasets[ds.name] = ds
            except Exception:
                logger.debug("Failed to load dataset %s", ds_id)

    if not datasets:
        return None

    from pygramattic_reports.builder import BuildConfig  # noqa: PLC0415

    config = BuildConfig(
        report_name=str(build_log_data.get("report_name", "Validation")),
        template=template,
        theme=theme,
        datasets=datasets,
        primary_dataset=next(iter(datasets), None),
    )

    try:
        builder = ReportBuilder(
            chart_engine=ChartEngine(),
            template_renderer=TemplateRenderer(),
        )
        report, _ = builder.build(config)
    except Exception:
        return None
    else:
        return report


def _try_claude_client(app_config: AppConfig) -> ClaudeClient | None:
    """Try to create a Claude client."""
    from pygramattic_reports.ai import ClaudeClient  # noqa: PLC0415

    client = ClaudeClient(app_config.claude)
    if client.is_available():
        return client
    return None


def _print_results(result: object) -> None:
    """Print validation results to the console."""
    from pygramattic_reports.models import ValidationResult  # noqa: PLC0415

    if not isinstance(result, ValidationResult):
        return

    console.print(f"\nValidation: {result.total_checks} checks")

    status_icons = {
        CheckStatus.PASS: "[green]\u2713[/green]",
        CheckStatus.FAIL: "[red]\u2717[/red]",
        CheckStatus.WARN: "[yellow]![/yellow]",
        CheckStatus.SKIP: "[dim]\u2298[/dim]",
    }

    for check in result.checks:
        icon = status_icons.get(check.status, "?")
        console.print(f"  {icon} {check.message}")

    overall_icon = status_icons.get(result.overall_status, "?")
    console.print(
        f"\nResult: {overall_icon} {result.overall_status.value.upper()} "
        f"({result.passed} passed, {result.failed} failed, "
        f"{result.warnings} warnings)"
    )
