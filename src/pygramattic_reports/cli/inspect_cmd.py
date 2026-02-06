"""CLI command for inspecting report resources.

Provides tools to view loaded datasets, manifests, and internal state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pygramattic_reports.logging import get_logger
from pygramattic_reports.models import Manifest

inspect_app = typer.Typer(
    name="inspect",
    help="Inspect report resources (datasets, manifests).",
    no_args_is_help=True,
)

logger = get_logger("cli.inspect")
console = Console()


@inspect_app.command("dataset")
def inspect_dataset(
    ctx: typer.Context,
    dataset_id: Annotated[str, typer.Argument(help="ID of the dataset to inspect")],
    rows: Annotated[int, typer.Option("--rows", "-n", help="Number of rows to show")] = 10,
) -> None:
    """View details and sample data for a specific dataset."""
    data_dir = ctx.obj.get("data_dir") or Path("data")

    # scan for manifest.json files
    found_manifest = None
    manifest_file = None

    if data_dir.exists():
        for path in data_dir.glob("**/manifest.json"):
            try:
                m = Manifest.model_validate_json(path.read_text())
                if m.id == dataset_id:
                    found_manifest = m
                    manifest_file = path
                    break
            except Exception:
                continue

    if not found_manifest:
        console.print(f"[red]Dataset '{dataset_id}' not found in {data_dir}.[/red]")
        raise typer.Exit(code=1)

    console.print(Panel(f"[bold blue]Dataset Inspector: {dataset_id}[/bold blue]"))
    console.print(f"Name: {found_manifest.name}")
    console.print(f"Type: {found_manifest.source_type}")
    console.print(f"Source: {found_manifest.source_path}")
    console.print(f"Storage: {found_manifest.storage_path}")
    console.print(f"Rows: {found_manifest.row_count}")
    console.print(f"Created: {found_manifest.created_at}")

    # Load and peek data
    # Assuming parquet for now as per Manifest default
    try:
        if manifest_file is None:
            # Should be unreachable due to check above, but for mypy:
            raise typer.Exit(code=1)

        data_path = manifest_file.parent / found_manifest.storage_path
        if not data_path.exists():
            console.print(f"[red]Data file missing at {data_path}[/red]")
            return

        import pandas as pd

        if found_manifest.format == "parquet":
            df = pd.read_parquet(data_path)
        elif found_manifest.format == "csv":
            df = pd.read_csv(data_path)
        else:
            console.print(
                f"[yellow]Preview not supported for format: {found_manifest.format}[/yellow]"
            )
            return

        # Show Schema
        table = Table(title="Schema")
        table.add_column("Column", style="cyan")
        table.add_column("Type", style="green")

        for col in found_manifest.columns:
            table.add_row(col.name, str(col.dtype))

        console.print(table)
        console.print("")

        # Show Data
        console.print(f"[bold]Sample Data ({rows} rows):[/bold]")

        sample = df.head(rows)
        data_table = Table(show_header=True, header_style="bold magenta")

        for col_name in sample.columns:
            data_table.add_column(str(col_name))

        for _, row in sample.iterrows():
            data_table.add_row(*[str(val) for val in row])

        console.print(data_table)

    except Exception as e:
        console.print(f"[red]Failed to load data:[/red] {e}")


@inspect_app.command("manifest")
def inspect_manifest(
    ctx: typer.Context,
) -> None:
    """List all available datasets in the data directory."""
    data_dir = ctx.obj.get("data_dir") or Path("data")

    if not data_dir.exists():
        console.print(f"[red]Data directory not found: {data_dir}[/red]")
        return

    table = Table(title=f"Datasets in {data_dir}")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Type")
    table.add_column("Rows", justify="right")
    table.add_column("Path")

    count = 0
    for path in data_dir.glob("**/manifest.json"):
        try:
            m = Manifest.model_validate_json(path.read_text())
            table.add_row(m.id, m.name, m.source_type, str(m.row_count), str(path.parent))
            count += 1
        except Exception:
            # console.print(f"[dim]Skipping invalid manifest at {path}: {e}[/dim]")
            pass

    if count == 0:
        console.print("No datasets found.")
    else:
        console.print(table)
