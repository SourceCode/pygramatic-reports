"""List command for the CLI.

Shows all ingested datasets, generated reports, available templates,
and available themes.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from pygramattic_reports.config import load_config
from pygramattic_reports.config.settings import StorageConfig
from pygramattic_reports.storage.manager import StorageManager

console = Console()

_VALID_RESOURCES = ("datasets", "reports", "templates", "themes")


def list_resources(
    ctx: typer.Context,
    resource: str | None = typer.Argument(
        "datasets",
        help="What to list: datasets, reports, templates, or themes",
    ),
) -> None:
    """List ingested datasets, reports, templates, or themes."""
    if resource not in _VALID_RESOURCES:
        console.print(
            f"[red]Error:[/red] Unknown resource {resource!r}. "
            f"Choose from: {', '.join(_VALID_RESOURCES)}"
        )
        raise typer.Exit(code=1)

    if resource == "datasets":
        _list_datasets(ctx)
    elif resource == "reports":
        console.print("[dim]No reports generated yet.[/dim]")
    elif resource == "templates":
        console.print("[dim]No templates available yet.[/dim]")
    else:
        console.print("[dim]No themes available yet.[/dim]")


def _list_datasets(ctx: typer.Context) -> None:
    """List all ingested datasets with a Rich table."""
    obj: dict[str, object] = ctx.obj or {}
    data_dir = obj.get("data_dir")
    config_path = obj.get("config_path")

    overrides: dict[str, object] = {}
    if data_dir is not None:
        overrides["storage"] = StorageConfig(data_dir=data_dir)

    config_dir = config_path.parent if isinstance(config_path, Path) else None
    app_config = load_config(config_dir=config_dir, overrides=overrides)

    storage = StorageManager(app_config)
    manifests = storage.list_datasets()

    if not manifests:
        console.print("[dim]No datasets found. Use 'report ingest' to add data.[/dim]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Source")
    table.add_column("Rows", justify="right")
    table.add_column("Columns", justify="right")
    table.add_column("Created")

    for m in manifests:
        created_str = m.created_at.strftime("%Y-%m-%d %H:%M")
        table.add_row(
            m.id[:8],
            m.name,
            m.source_type,
            str(m.row_count),
            str(len(m.columns)),
            created_str,
        )

    console.print(table)
