# Pygramattic Reports

> Unified Python Report Processing & Generation Tool

A comprehensive, clonable Python-based tool that ingests data from many sources, normalizes it, processes it, and generates consistent, validated, and well-styled reports across multiple output formats.

## Key Capabilities

*   **Universal Ingestion**: Support for JSON, CSV, Excel, DOCX, Google Docs, Sheets, and Slides.
*   **Strict Normalization**: All inputs are normalized to a canonical JSON schema before processing.
*   **Template-Driven**: Jinja2-based templating engine for consistent report structure.
*   **Publication-Quality Charts**: Integrated Matplotlib, Seaborn, and Plotly support.
*   **Validation Guarantee**: Automated verification of report content against source data.
*   **Feedback Loops**: AI-driven analysis of manual edits to improve future generation.

## Architecture Summary

The system follows a strict linear pipeline:

`Inputs` → `Loaders` → `Normalizers` → `Processors` → `Builders` → `Validators` → `Outputs`

*   **Loaders**: Handle file I/O and external API authentication.
*   **Normalizers**: Standardize disparate input formats.
*   **Processors**: Apply business logic and transformations.
*   **Builders**: Assemble the final report using templates and themes.
*   **Validators**: Ensure data integrity in the final output.

See [Architecture & Implementation](/docs/implementation.md) for deeper details.

## Tech Stack

*   **Runtime**: Python 3.11+
*   **Core Framework**: Pydantic 2.0+ (Validation), Pandas 2.0+ (Data Processing)
*   **CLI**: Typer + Rich
*   **Visualization**: Matplotlib, Seaborn, OpenPyXL
*   **Templating**: Jinja2, Mistune
*   **Linting/Quality**: Ruff, MyPy (Strict)

## Quick Start

### Prerequisites
*   Python 3.11 or higher
*   `hatch` (recommended) or `pip`

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pygramattic-reports.git
cd pygramattic-reports

# Install dependencies
pip install -e ".[dev,all]"
```

### Running Your First Report

```bash
# Initialize a new project structure
report init my-first-report
cd my-first-report

# Ingest sample data
report ingest ./data/sample.csv

# Build the report
report build --config config.yaml
```

See [Installation Guide](/docs/install.md) and [First Run](/docs/first-run.md) for more details.

## Configuration

Configuration is managed via YAML files and environment variables.

Example `.env`:
```bash
GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
LOG_LEVEL="INFO"
DATA_DIR="./data"
```

See [Setup Guide](/docs/setup.md) for full configuration details.

## Testing & Coverage

We enforce strict test coverage and type safety.

```bash
# Run unit tests
pytest tests/unit

# Run full suite with coverage
pytest --cov=src/pygramattic_reports tests/
```

See [Testing Guide](/docs/testing.md) and [Coverage Report](/docs/coverage.md).

## Documentation Index

### Core
*   [Documentation Hub](/docs/README.md)
*   [Installation](/docs/install.md)
*   [Setup & Configuration](/docs/setup.md)
*   [First Run Guide](/docs/first-run.md)

### Technical
*   [Functionality & Workflows](/docs/functionality.md)
*   [Data Schema](/docs/schema.md)
*   [API Reference](/docs/api.md)
*   [Integrations](/docs/integrations.md)
*   [Implementation Details](/docs/implementation.md)

### Operational
*   [Testing Strategy](/docs/testing.md)
*   [Code Coverage](/docs/coverage.md)
*   [Troubleshooting](/docs/troubleshooting.md)
*   [Security & Auth](/docs/security.md)
*   [Contributing](/docs/contributing.md)
*   [Changelog](/docs/changelog.md)

## Contributing

We welcome contributions! Please see [Contributing Guide](/docs/contributing.md) for our workflow, style guide, and review process.

## License

MIT License. See `pyproject.toml` for details.
