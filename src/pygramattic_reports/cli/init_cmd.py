"""Init command for the CLI.

Scaffolds a new report configuration file that users can edit.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

console = Console()

_CONFIG_TEMPLATE = """\
# Report Configuration
# Edit this file to configure your report build

report:
  name: "My Report"
  template: default           # Template name from templates_dir
  theme: default              # Theme name from themes_dir

  datasets:
    # Map dataset names to dataset IDs from 'report list datasets'
    main_data: "<dataset_id>"

  output:
    formats:
      - md                    # Markdown
      # - docx               # Word document
    directory: data/reports/

  ai:
    enabled: false            # Set to true to use Claude CLI for narrative
    sections:
      - summary
"""


def init(
    output: str | None = typer.Option(
        "report_config.yaml",
        "--output",
        "-o",
        help="Output path for the config file",
    ),
) -> None:
    """Scaffold a new report configuration file."""
    out_path = Path(output or "report_config.yaml")

    if out_path.exists():
        console.print(f"[yellow]Warning:[/yellow] {out_path} already exists, overwriting.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_CONFIG_TEMPLATE)

    console.print(f"[green]\u2713[/green] Created {out_path}")
    console.print("  Edit this file, then run [bold]report build report_config.yaml[/bold]")
