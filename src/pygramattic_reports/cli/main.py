"""CLI entrypoint for pygramattic-reports.

Defines the ``report`` command with global options and registers
all sub-commands (ingest, list, init).
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from pygramattic_reports import __version__

app = typer.Typer(
    name="report",
    help="Pygramattic Reports - Unified Report Processing & Generation Tool",
    no_args_is_help=True,
)
console = Console()


def _version_callback(value: bool) -> None:
    """Print version and exit when ``--version`` is passed."""
    if value:
        console.print(f"pygramattic-reports {__version__}")
        raise typer.Exit


@app.callback()
def main(
    ctx: typer.Context,
    config: str | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable debug logging",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress info output",
    ),
    data_dir: str | None = typer.Option(
        None,
        "--data-dir",
        help="Override data directory path",
    ),
    _version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Pygramattic Reports - Unified Report Processing & Generation Tool."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = Path(config) if config else None
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["data_dir"] = Path(data_dir) if data_dir else None


# Register sub-commands -------------------------------------------------------

from .build_cmd import build  # noqa: E402
from .export_cmd import export  # noqa: E402
from .feedback_cmd import feedback  # noqa: E402
from .ingest import ingest  # noqa: E402
from .init_cmd import init  # noqa: E402
from .list_cmd import list_resources  # noqa: E402
from .validate_cmd import validate  # noqa: E402

app.command()(ingest)
app.command("list")(list_resources)
app.command()(init)
app.command()(build)
app.command()(export)
app.command()(validate)
app.command()(feedback)
