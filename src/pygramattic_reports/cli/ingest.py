"""Ingest command for the CLI.

Loads a data file, normalizes it, and saves the resulting
dataset to storage.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.table import Table

from pygramattic_reports.config import load_config
from pygramattic_reports.config.settings import StorageConfig
from pygramattic_reports.loaders import create_default_registry
from pygramattic_reports.models import ContentType, FileSourceConfig, SourceConfig, SourceType
from pygramattic_reports.normalizers import DocumentNormalizer, TabularNormalizer
from pygramattic_reports.storage.manager import StorageManager

if TYPE_CHECKING:
    from pygramattic_reports.config.settings import AppConfig
    from pygramattic_reports.models.dataset import Dataset
    from pygramattic_reports.models.raw_data import RawData

console = Console()

_EXTENSION_MAP: dict[str, str] = {
    ".csv": "csv",
    ".json": "json",
    ".xlsx": "xlsx",
    ".docx": "docx",
    ".txt": "txt",
    ".md": "md",
    ".markdown": "md",
}


def ingest(
    ctx: typer.Context,
    source_path: str = typer.Argument(..., help="Path to the data file to ingest"),
    format: str | None = typer.Option(  # noqa: A002
        None,
        "--format",
        "-f",
        help="Force input format (csv, json, xlsx, docx, txt, md)",
    ),
    name: str | None = typer.Option(
        None,
        "--name",
        "-n",
        help="Human-readable name for this dataset",
    ),
    sheet: str | None = typer.Option(
        None,
        "--sheet",
        help="Sheet name for XLSX files",
    ),
    delimiter: str = typer.Option(",", "--delimiter", help="CSV field delimiter"),
    encoding: str = typer.Option("utf-8", "--encoding", help="File encoding"),
    no_header: bool = typer.Option(
        False,
        "--no-header",
        help="Treat first row as data, not headers",
    ),
) -> None:
    """Ingest a data file into the storage system.

    Reads the file, normalizes the data, infers types, and saves
    the resulting dataset for use in report building.
    """
    path = Path(source_path).resolve()

    if not path.is_file():
        console.print(f"[red]Error:[/red] File not found: {path}")
        raise typer.Exit(code=1)

    # Detect format
    source_type_str = format or _detect_format(path)
    if source_type_str is None:
        console.print(f"[red]Error:[/red] Cannot detect format for {path.suffix!r}. Use --format.")
        raise typer.Exit(code=1)

    try:
        source_type = SourceType(source_type_str)
    except ValueError:
        console.print(f"[red]Error:[/red] Unsupported format: {source_type_str!r}")
        raise typer.Exit(code=1) from None

    # Build config
    dataset_name = name or path.stem
    file_config = FileSourceConfig(
        path=path,
        encoding=encoding,
        sheet_name=sheet,
        delimiter=delimiter,
        has_header=not no_header,
    )
    source_config = SourceConfig(
        source_type=source_type,
        name=dataset_name,
        file=file_config,
    )

    # Load
    quiet = ctx.obj.get("quiet", False) if ctx.obj else False
    registry = create_default_registry()
    loader = registry.get_loader(source_type)

    try:
        raw_data = loader.load(source_config)
    except Exception as exc:
        console.print(f"[red]Error loading file:[/red] {exc}")
        raise typer.Exit(code=1) from None

    if not quiet:
        row_info = f", {raw_data.row_count} rows" if raw_data.row_count else ""
        console.print(
            f"[green]\u2713[/green] Loaded: {path.name} ({source_type_str.upper()}{row_info})"
        )

    # Normalize
    try:
        dataset = _normalize(raw_data)
    except Exception as exc:
        console.print(f"[red]Error normalizing data:[/red] {exc}")
        raise typer.Exit(code=1) from None

    if not quiet:
        console.print(f"[green]\u2713[/green] Normalized: {len(dataset.schema)} columns detected")

    # Save
    app_config = _load_app_config(ctx)
    storage = StorageManager(app_config)
    storage.initialize()

    try:
        storage.save_dataset(dataset)
    except Exception as exc:
        console.print(f"[red]Error saving dataset:[/red] {exc}")
        raise typer.Exit(code=1) from None

    if not quiet:
        save_dir = app_config.storage.data_dir / app_config.storage.processed_dir / dataset.id
        console.print(f"[green]\u2713[/green] Saved: dataset {dataset.id[:8]} \u2192 {save_dir}")
        _print_schema_table(dataset)


def _detect_format(path: Path) -> str | None:
    """Auto-detect source format from file extension."""
    return _EXTENSION_MAP.get(path.suffix.lower())


def _normalize(raw_data: RawData) -> Dataset:
    """Choose the appropriate normalizer and normalize."""
    if raw_data.content_type == ContentType.TABULAR:
        return TabularNormalizer().normalize(raw_data)
    return DocumentNormalizer().normalize(raw_data)


def _load_app_config(ctx: typer.Context) -> AppConfig:
    """Build AppConfig from CLI context options."""
    obj: dict[str, object] = ctx.obj or {}
    config_path = obj.get("config_path")
    data_dir = obj.get("data_dir")

    overrides: dict[str, object] = {}
    if data_dir is not None:
        overrides["storage"] = StorageConfig(data_dir=data_dir)

    config_dir = config_path.parent if isinstance(config_path, Path) else None
    return load_config(config_dir=config_dir, overrides=overrides)


def _print_schema_table(dataset: Dataset) -> None:
    """Print a Rich table summarizing the dataset schema."""
    table = Table(show_header=True, header_style="bold")
    table.add_column("Column")
    table.add_column("Type")
    table.add_column("Nulls", justify="right")

    for col in dataset.schema:
        if col.name in dataset.dataframe.columns:
            null_count = int(dataset.dataframe[col.name].isna().sum())
        else:
            null_count = 0
        table.add_row(col.name, col.dtype.value, str(null_count))

    console.print()
    console.print(table)
