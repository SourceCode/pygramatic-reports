# Phase 08: CLI Foundation & Ingest Command

## Objective

Build the CLI framework using Typer and implement the first user-facing command: `report ingest`. This command ingests data files, normalizes them, and persists them to storage -- completing the first user-visible workflow.

## Why This Phase Is Eighth

With loaders, normalizers, and storage working, we can now expose the ingestion pipeline to users via the CLI. This is the first command users will run and validates the entire data input path end-to-end.

## Tasks

### Task 8.1: Set Up the CLI Application

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/cli/main.py`

**Description:** Create the main Typer application with global options and the application entrypoint.

**Requirements:**
- Use `typer` as the CLI framework
- Use `rich` for terminal output formatting (tables, progress bars, status messages)
- Global options: `--config` (path to config file), `--verbose` (enable DEBUG logging), `--quiet` (suppress INFO output), `--data-dir` (override data directory)
- Application name: `report`
- Version callback: `--version` flag

```python
import typer
from rich.console import Console

app = typer.Typer(
    name="report",
    help="Unified Python Report Processing & Generation Tool",
    no_args_is_help=True,
)
console = Console()


@app.callback()
def main(
    config: str = typer.Option(None, "--config", "-c", help="Path to config file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress info output"),
    data_dir: str = typer.Option(None, "--data-dir", help="Override data directory path"),
):
    """Pygramattic Reports - Unified Report Processing & Generation."""
    ...


# Register sub-commands from other modules
# app.command()(ingest)
# app.command()(build)
# etc.
```

---

### Task 8.2: Implement the `ingest` Command

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/cli/ingest.py`

**Description:** The `report ingest` command loads a data file, normalizes it, and saves it to storage.

**Interface:**
```
report ingest <source_path> [OPTIONS]

Arguments:
  source_path    Path to the data file to ingest

Options:
  --format, -f    Force input format (auto-detected from extension if omitted)
  --name, -n      Human-readable name for this dataset (defaults to filename)
  --sheet         Sheet name for XLSX files
  --delimiter     Field delimiter for CSV files (default: ",")
  --encoding      File encoding (default: "utf-8")
  --no-header     Treat first row as data, not headers
```

**Workflow:**
1. Resolve file path, verify file exists
2. Auto-detect format from file extension (or use `--format`)
3. Build `SourceConfig` from CLI arguments
4. Get loader from registry
5. Load the file → `RawData`
6. Normalize → `Dataset`
7. Save to storage via `StorageManager`
8. Print summary: dataset ID, row count, column names, inferred types

**Example output:**
```
$ report ingest data/sales.csv --name "Q4 Sales"

✓ Loaded: data/sales.csv (CSV, 150 rows)
✓ Normalized: 5 columns detected

  Column       Type      Nulls
  ─────────────────────────────
  region       string    0
  revenue      float     0
  quarter      string    0
  growth_pct   float     0
  is_active    boolean   3

✓ Saved: dataset abc12345 → data/processed/abc12345/
```

**Implementation:**
```python
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


def ingest(
    source_path: str = typer.Argument(..., help="Path to the data file to ingest"),
    format: str = typer.Option(None, "--format", "-f", help="Force input format"),
    name: str = typer.Option(None, "--name", "-n", help="Dataset name"),
    sheet: str = typer.Option(None, "--sheet", help="Sheet name (XLSX only)"),
    delimiter: str = typer.Option(",", "--delimiter", help="CSV delimiter"),
    encoding: str = typer.Option("utf-8", "--encoding", help="File encoding"),
    no_header: bool = typer.Option(False, "--no-header", help="No header row"),
):
    """Ingest a data file into the storage system.

    Reads the file, normalizes the data, infers types, and saves
    the resulting dataset for use in report building.
    """
    path = Path(source_path)

    if not path.exists():
        console.print(f"[red]Error:[/red] File not found: {path}")
        raise typer.Exit(1)

    # 1. Detect format
    source_type = format or _detect_format(path)

    # 2. Build config
    config = _build_source_config(path, source_type, name, sheet, delimiter, encoding, no_header)

    # 3. Load
    with console.status("Loading file..."):
        registry = create_default_registry()
        loader = registry.get_loader(SourceType(source_type))
        raw_data = loader.load(config)

    console.print(f"[green]✓[/green] Loaded: {path} ({source_type.upper()}, {raw_data.row_count} rows)")

    # 4. Normalize
    with console.status("Normalizing data..."):
        normalizer = _get_normalizer(raw_data)
        dataset = normalizer.normalize(raw_data)

    # 5. Save
    with console.status("Saving to storage..."):
        storage = StorageManager(config)
        storage.initialize()
        storage.save_dataset(dataset)

    # 6. Print summary
    _print_dataset_summary(dataset)
```

---

### Task 8.3: Implement the `list` Command

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/cli/list_cmd.py`

**Description:** The `report list` command shows all ingested datasets, generated reports, available templates, and available themes.

**Interface:**
```
report list [datasets|reports|templates|themes]

Arguments:
  resource    What to list (default: datasets)
```

**Example output:**
```
$ report list datasets

  ID          Name           Source   Rows   Columns   Created
  ──────────────────────────────────────────────────────────────
  abc12345    Q4 Sales       csv      150    5         2024-12-01 14:30
  def67890    Revenue Data   xlsx     500    8         2024-12-02 09:15
```

---

### Task 8.4: Implement the `init` Command

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/cli/init_cmd.py`

**Description:** The `report init` command scaffolds a new report configuration file.

**Interface:**
```
report init [--output report_config.yaml]
```

**Behavior:**
- Create a commented `report_config.yaml` file that users can edit
- Include placeholders for datasets, template, theme, output formats

**Generated file example:**
```yaml
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
```

---

### Task 8.5: Wire CLI Commands Together

**File to update:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/cli/main.py`

Register all commands in the main app:
```python
from .ingest import ingest
from .list_cmd import list_resources
from .init_cmd import init

app.command()(ingest)
app.command("list")(list_resources)
app.command()(init)
```

---

### Task 8.6: Create CLI Package Init

**File to create/update:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/cli/__init__.py`

```python
"""Command-line interface for pygramattic-reports.

Usage:
    report ingest data.csv
    report list datasets
    report init
    report build config.yaml
    report validate report.docx
"""
from .main import app

__all__ = ["app"]
```

---

### Task 8.7: Write CLI Tests

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_cli.py`

**Requirements:** Use `typer.testing.CliRunner` for testing CLI commands.

**Test cases:**
1. `test_ingest_csv` -- Ingest a CSV file, verify dataset is saved
2. `test_ingest_json` -- Ingest a JSON file
3. `test_ingest_file_not_found` -- Proper error for missing file
4. `test_ingest_unknown_format` -- Proper error for unsupported format
5. `test_ingest_with_name` -- Custom dataset name
6. `test_list_datasets_empty` -- No datasets returns clean output
7. `test_list_datasets_after_ingest` -- Lists ingested dataset
8. `test_init_creates_config` -- Creates report_config.yaml
9. `test_version_flag` -- `--version` shows version
10. `test_help_flag` -- `--help` shows usage info

**Example:**
```python
from typer.testing import CliRunner
from pygramattic_reports.cli import app

runner = CliRunner()


def test_ingest_csv(tmp_path, sample_csv):
    result = runner.invoke(app, [
        "ingest", str(sample_csv),
        "--data-dir", str(tmp_path),
        "--name", "test_data",
    ])
    assert result.exit_code == 0
    assert "Loaded" in result.stdout
    assert "Saved" in result.stdout
```

---

## Dependencies

- **Depends on:** Phase 06 (loaders), Phase 07 (extended loaders), Phase 05 (storage)
- **Blocks:** Phase 16 (build command)

## Acceptance Criteria

1. `report ingest <file>` loads, normalizes, and saves data files
2. Auto-detection works for all supported file extensions
3. `report list datasets` shows all ingested datasets
4. `report init` creates a report config template
5. Error messages are user-friendly (no raw stack traces)
6. All CLI tests pass
7. `report --help` shows all available commands

## References

- PRD CLI Interface: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 373-381)
- PRD CLI Example: `report ingest data.csv` (line 377)
