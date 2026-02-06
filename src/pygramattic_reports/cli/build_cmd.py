"""Build command for the CLI.

Orchestrates the full report-build pipeline: load config,
resolve references, build report, and write output files.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console

from pygramattic_reports.builder import ReportBuilder, load_build_config
from pygramattic_reports.charts import ChartEngine
from pygramattic_reports.config import load_config
from pygramattic_reports.config.settings import StorageConfig
from pygramattic_reports.outputs import MarkdownAdapter, create_default_output_registry
from pygramattic_reports.storage.manager import StorageManager
from pygramattic_reports.templates import TemplateRenderer

if TYPE_CHECKING:
    from pygramattic_reports.ai import ClaudeClient
    from pygramattic_reports.builder.config import BuildConfig
    from pygramattic_reports.config import AppConfig
    from pygramattic_reports.logging import BuildLog
    from pygramattic_reports.models import Report, ThemeSpec

console = Console()


def build(
    ctx: typer.Context,
    config_path: str = typer.Argument(..., help="Path to report_config.yaml"),
    output_format: list[str] | None = typer.Option(
        None,
        "--output-format",
        "-o",
        help="Output format(s) — repeatable (md, docx, xlsx)",
    ),
    output_dir: str | None = typer.Option(
        None,
        "--output-dir",
        help="Override output directory",
    ),
    no_ai: bool = typer.Option(False, "--no-ai", help="Disable AI sections"),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview what would be generated without writing files",
    ),
    template: str | None = typer.Option(
        None,
        "--template",
        help="Override template name",
    ),
    theme: str | None = typer.Option(
        None,
        "--theme",
        help="Override theme name",
    ),
) -> None:
    """Build a report from a configuration file.

    Takes a report_config.yaml that specifies the template, theme,
    datasets, and output formats.  Produces one or more report files.
    """
    config_file = Path(config_path)
    if not config_file.exists():
        console.print(f"[red]Error:[/red] Config file not found: {config_file}")
        raise typer.Exit(code=1)

    quiet = ctx.obj.get("quiet", False) if ctx.obj else False
    app_config = _load_app_config(ctx)
    storage = StorageManager(app_config)
    storage.initialize()

    build_config = _resolve_build_config(
        config_file,
        app_config,
        storage,
        output_format,
        output_dir,
        template,
        theme,
        no_ai,
    )

    if not quiet:
        _print_plan(build_config)

    if dry_run:
        console.print("\n[yellow]Dry run[/yellow] — no files written.")
        return

    report, build_log = _run_build(build_config, app_config, quiet)
    if not quiet:
        console.print(
            f"\n[green]\u2713[/green] Built: {build_log.sections_generated} sections"
            f" ({build_log.sections_skipped} skipped)"
        )

    _write_outputs(report, build_config, build_log, storage, quiet)


# -- Internal helpers ---------------------------------------------------------


def _resolve_build_config(
    config_file: Path,
    app_config: AppConfig,
    storage: StorageManager,
    output_format: list[str] | None,
    output_dir: str | None,
    template_name: str | None,
    theme_name: str | None,
    no_ai: bool,
) -> BuildConfig:
    """Load and optionally override the build config."""
    try:
        build_config = load_build_config(config_file, app_config, storage)
    except Exception as exc:
        console.print(f"[red]Error loading build config:[/red] {exc}")
        raise typer.Exit(code=1) from None

    return _apply_overrides(
        build_config,
        app_config,
        output_format,
        output_dir,
        template_name,
        theme_name,
        no_ai,
    )


def _run_build(
    build_config: BuildConfig,
    app_config: AppConfig,
    quiet: bool,
) -> tuple[Report, BuildLog]:
    """Execute the report build."""
    claude_client = _init_claude_client(build_config, app_config, quiet)
    try:
        builder = ReportBuilder(
            chart_engine=ChartEngine(),
            template_renderer=TemplateRenderer(),
            claude_client=claude_client,
        )
        return builder.build(build_config)
    except Exception as exc:
        console.print(f"[red]Build error:[/red] {exc}")
        raise typer.Exit(code=1) from None


def _init_claude_client(
    build_config: BuildConfig,
    app_config: AppConfig,
    quiet: bool,
) -> ClaudeClient | None:
    """Initialize Claude client if AI is enabled and available."""
    if not build_config.ai_enabled:
        if not quiet:
            console.print("  AI: Disabled")
        return None

    from pygramattic_reports.ai import ClaudeClient  # noqa: PLC0415

    client = ClaudeClient(app_config.claude)
    if not client.is_available():
        if not quiet:
            console.print(
                "  AI: [yellow]Unavailable[/yellow] (Claude CLI not found, using fallbacks)"
            )
        return None

    if not quiet:
        console.print("  AI: [green]Enabled[/green] (Claude CLI available)")
    return client


def _write_outputs(
    report: Report,
    build_config: BuildConfig,
    build_log: BuildLog,
    storage: StorageManager,
    quiet: bool,
) -> None:
    """Write output files and build log."""
    report_id = report.id
    registry = create_default_output_registry()

    for fmt in build_config.output_formats:
        try:
            adapter = registry.get_adapter(fmt)
        except ValueError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            continue

        content = adapter.render(report, build_config.theme)
        filename = f"report{adapter.file_extension()}"

        if isinstance(adapter, MarkdownAdapter) and _has_media(report):
            _save_markdown_media(adapter, report, build_config.theme, storage, report_id)

        out_path = storage.save_report(report_id, content, filename)
        if not quiet:
            console.print(f"[green]\u2713[/green] {out_path}")

    log_dict = build_log.model_dump(mode="json")
    storage.save_report(report_id, b"", "_placeholder_", build_log=log_dict)

    if not quiet:
        log_dir = storage._resolve_stage_dir("reports") / report_id  # noqa: SLF001
        console.print(f"[green]\u2713[/green] {log_dir / 'build_log.json'}")

        warnings = build_log.sections_skipped
        w_text = f", {warnings} warnings" if warnings else ""
        console.print(
            f"\nReport built successfully: {build_log.sections_generated} sections{w_text}"
        )


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


def _apply_overrides(
    build_config: BuildConfig,
    app_config: AppConfig,
    output_format: list[str] | None,
    output_dir: str | None,
    template_name: str | None,
    theme_name: str | None,
    no_ai: bool,
) -> BuildConfig:
    """Apply CLI flag overrides to the build config."""
    from pygramattic_reports.templates import TemplateLoader  # noqa: PLC0415
    from pygramattic_reports.themes import ThemeLoader  # noqa: PLC0415

    updates: dict[str, object] = {}

    if output_format:
        updates["output_formats"] = output_format
    if output_dir:
        updates["output_directory"] = output_dir
    if no_ai:
        updates["ai_enabled"] = False

    if template_name:
        loader = TemplateLoader(templates_dir=app_config.templates_dir)
        updates["template"] = loader.load(template_name)

    if theme_name:
        loader_t = ThemeLoader(themes_dir=app_config.themes_dir)
        updates["theme"] = loader_t.load(theme_name)

    if updates:
        return build_config.model_copy(update=updates)
    return build_config


def _print_plan(config: BuildConfig) -> None:
    """Print a short summary of the build plan."""
    console.print(f"\nBuilding report: [bold]{config.report_name}[/bold]")
    console.print(f"  Template: {config.template.name}")
    console.print(f"  Theme: {config.theme.name}")
    ds_info = ", ".join(f"{n} ({d.row_count} rows)" for n, d in config.datasets.items())
    console.print(f"  Datasets: {ds_info}")
    console.print(f"  Formats: {', '.join(config.output_formats)}")


def _has_media(report: Report) -> bool:
    """Check whether the report contains any media sections."""
    from pygramattic_reports.models import SectionType  # noqa: PLC0415

    return any(
        s.section_type in (SectionType.CHART, SectionType.IMAGE) and s.media_bytes
        for s in report.sections
    )


def _save_markdown_media(
    adapter: MarkdownAdapter,
    report: Report,
    theme: ThemeSpec,
    storage: StorageManager,
    report_id: str,
) -> None:
    """Save chart images referenced by the markdown adapter."""
    media_dir = storage._resolve_stage_dir("media") / report_id  # noqa: SLF001
    media_dir.mkdir(parents=True, exist_ok=True)
    adapter._media_dir = media_dir  # noqa: SLF001
    adapter._media_files = []  # noqa: SLF001
    adapter.render(report, theme)
    for filename, data in adapter._media_files:  # noqa: SLF001
        (media_dir / filename).write_bytes(data)
