"""Export command for the CLI.

Converts a stored dataset to a different format (JSON, CSV, SQL)
and writes to a file or stdout.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console

from pygramattic_reports.config import load_config
from pygramattic_reports.config.settings import StorageConfig
from pygramattic_reports.converters import to_csv, to_json, to_sql
from pygramattic_reports.storage.manager import StorageManager

if TYPE_CHECKING:
    from pygramattic_reports.config import AppConfig

console = Console()

_FORMAT_MAP = {
    "json": to_json,
    "csv": to_csv,
    "sql": to_sql,
}


def export(
    ctx: typer.Context,
    dataset_id: str = typer.Argument(..., help="ID of the dataset to export"),
    format: str = typer.Option(  # noqa: A002
        ...,
        "--format",
        "-f",
        help="Output format: json, csv, sql",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: stdout)",
    ),
    dialect: str = typer.Option(
        "postgresql",
        "--dialect",
        help="SQL dialect: postgresql, sqlite",
    ),
    layout: str = typer.Option(
        "records",
        "--layout",
        help="JSON layout: records, columnar",
    ),
    delimiter: str = typer.Option(",", "--delimiter", help="CSV delimiter"),
) -> None:
    """Export a stored dataset to JSON, CSV, or SQL.

    Reads a dataset from storage and converts it to the requested
    format. Output goes to a file (--output) or stdout.
    """
    if format not in _FORMAT_MAP:
        console.print(
            f"[red]Error:[/red] Unsupported format {format!r}. "
            f"Use one of: {', '.join(sorted(_FORMAT_MAP))}"
        )
        raise typer.Exit(code=1)

    # Load app config & storage
    app_config = _load_app_config(ctx)
    storage = StorageManager(app_config)
    storage.initialize()

    # Load dataset
    try:
        dataset = storage.load_dataset(dataset_id)
    except Exception as exc:
        console.print(f"[red]Error loading dataset:[/red] {exc}")
        raise typer.Exit(code=1) from None

    # Convert
    try:
        result = _convert(dataset, format, dialect=dialect, layout=layout, delimiter=delimiter)
    except Exception as exc:
        console.print(f"[red]Error converting dataset:[/red] {exc}")
        raise typer.Exit(code=1) from None

    # Write output
    quiet = ctx.obj.get("quiet", False) if ctx.obj else False

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result, encoding="utf-8")
        if not quiet:
            console.print(
                f"[green]\u2713[/green] Exported dataset {dataset_id[:8]} "
                f"to {out_path} ({format.upper()}, {dataset.row_count} rows)"
            )
    else:
        sys.stdout.write(result)


def _convert(
    dataset: object,
    fmt: str,
    dialect: str = "postgresql",
    layout: str = "records",
    delimiter: str = ",",
) -> str:
    """Dispatch to the appropriate converter."""
    if fmt == "json":
        return to_json(dataset, layout=layout)  # type: ignore[arg-type]
    if fmt == "sql":
        return to_sql(dataset, dialect=dialect)  # type: ignore[arg-type]
    return to_csv(dataset, delimiter=delimiter)  # type: ignore[arg-type]


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
