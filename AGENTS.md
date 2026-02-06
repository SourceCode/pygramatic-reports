# AGENTS.md

## 🤖 AI Agent Usage Guide

This section is strictly for AI agents to understand how to effectively work within this repository.

### 1. Project Architecture

```mermaid
graph TD
    CLI[CLI (Typer)] --> Config[AppConfig (Pydantic)]
    Config --> Storage[Storage Engine]
    
    CLI --> Ingest[Ingestion]
    Ingest --> RawData[(Raw Data)]
    RawData --> Normalize[Normalization]
    Normalize --> Processed[(Processed Data)]
    
    Processed --> Build[Builder Engine]
    Templates[Jinja2 Templates] --> Build
    Themes[Themes] --> Build
    
    Build --> ReportObj[Report Object]
    ReportObj --> Validate[Validator]
    Validate --> Output[Output Adapters]
    
    Output --> Markdown[Markdown]
    Output --> PDF[PDF/DOCX]
    Output --> HTML[HTML]
```

### 2. Agent Quick Actions

Run these commands to verify your work.

**Environment Setup**
```bash
./scripts/agent_setup.sh
```

**Dump Configuration Schema**
```bash
python3 scripts/dump_schema.py
```

**Run Tests**
```bash
pytest tests/
```

**Lint & Format**
```bash
ruff check .
ruff format .
```

**Type Check**
```bash
mypy .
```

### 3. Verification Protocol (MANDATORY)

Before submitting any code changes, you **MUST** pass this checklist:

1.  [ ] **Linting**: No errors from `ruff check src`.
2.  [ ] **Type Safety**: No errors from `mypy src`.
3.  [ ] **Tests**: All tests pass (`pytest`). New logic must have new tests.
4.  [ ] **Schema**: If you changed models, verify `python3 scripts/dump_schema.py` still works.
5.  [ ] **Documentation**: Update docstrings for any modified functions.

### 4. Troubleshooting Guide

| Error Code | Context | Fix |
| :--- | :--- | :--- |
| `pydantic.ValidationError` | Runtime | Ensure input data matches strict schema types. |
| `F401` | Ruff | Remove unused imports. |
| `ANN101` | Ruff | Add missing type hints to function arguments (self, cls excluded). |
| `ModuleNotFoundError` | Python | Run `./scripts/agent_setup.sh` to install deps. |
| `mypy: Call to untyped function` | Mypy | Add type stubs or cast to known type if external lib is untyped. |

### 5. Project Map

```text
/
├── configs/          # Runtime configurations (YAML)
├── data/             # Data storage (Git-ignored)
├── docs/             # User documentation
├── scripts/          # Helper scripts for Agents
│   ├── agent_setup.sh
│   └── dump_schema.py
├── src/
│   └── pygramattic_reports/
│       ├── cli/      # Typer CLI commands
│       ├── config/   # Pydantic settings
│       ├── models/   # Core data models
│       ├── loaders/  # Input file parsers
│       └── ...
├── tests/            # Pytest suite
├── pyproject.toml    # Dependencies & Tool Config
└── AGENTS.md         # YOU ARE HERE
```

### 6. Contribution Rules

1.  **Strict Typing**: usage of `Any` is discouraged. Use specific types.
2.  **No Magic Numbers**: Define constants for literals.
3.  **Docstrings**: Google-style docstrings are required for all public members.
4.  **PathLib**: Use `pathlib.Path` instead of `os.path`.
5.  **Exceptions**: Define custom exceptions in `src/pygramattic_reports/exceptions.py`.

---

## Technical Reference: Pygramattic Reports

### Capabilities Mapping

| Feature | Description | Source Component |
| :--- | :--- | :--- |
| **Ingestion** | Loads data from diverse formats (JSON, CSV, Excel, DOCX, Google Docs) into memory. | `src/pygramattic_reports/loaders` |
| **Normalization** | Standardizes raw input data into a canonical internal JSON representation. | `src/pygramattic_reports/normalizers` |
| **Conversion** | Transforms canonical datasets into specific output formats (JSON, SQL). | `src/pygramattic_reports/converters` |
| **Processing** | Performs data transformations, aggregations, and metric logic using Pandas. | `src/pygramattic_reports/processors` |
| **Templating** | Renders report structure using Jinja2 templates, injecting processed data. | `src/pygramattic_reports/templates` |
| **Charting** | Generates visualizations (PNG/SVG) using Matplotlib and Seaborn. | `src/pygramattic_reports/charts` |
| **Building** | Orchestrates the assembly of full reports from templates, data, and assets. | `src/pygramattic_reports/builder` |
| **Validation** | Verifies generated report content against source data for accuracy. | `src/pygramattic_reports/validator` |
| **Feedback** | Analyzes report diffs to improve future generation logic. | `src/pygramattic_reports/feedback` |

### Operational Guidance

The primary interface is the `report` CLI tool.

#### CLI Commands

*   **Initialize Project**
    *   **Command**: `report init [OPTIONS]`
    *   **Description**: Scaffolds a new report project structure.
    *   **Source**: `src/pygramattic_reports/cli/init_cmd.py`

*   **Ingest Data**
    *   **Command**: `report ingest [FILE_PATH] [OPTIONS]`
    *   **Description**: Reads a source file and normalizes it into the `data/` directory.
    *   **Source**: `src/pygramattic_reports/cli/ingest.py`

*   **List Resources**
    *   **Command**: `report list [OPTIONS]`
    *   **Description**: Displays available datasets, templates, and reports.
    *   **Source**: `src/pygramattic_reports/cli/list_cmd.py`

*   **Build Report**
    *   **Command**: `report build --config [CONFIG_PATH] [OPTIONS]`
    *   **Description**: Generates a report based on a YAML configuration file.
    *   **Source**: `src/pygramattic_reports/cli/build_cmd.py`

*   **Export Data**
    *   **Command**: `report export [DATASET_ID] --format [FORMAT] [OPTIONS]`
    *   **Description**: Exports specific datasets to supported formats (CSV, JSON, SQL).
    *   **Source**: `src/pygramattic_reports/cli/export_cmd.py`

*   **Validate Report**
    *   **Command**: `report validate [REPORT_PATH] [OPTIONS]`
    *   **Description**: Strict verification of a generated report against its source data.
    *   **Source**: `src/pygramattic_reports/cli/validate_cmd.py`

*   **Process Feedback**
    *   **Command**: `report feedback [EDITED_REPORT_PATH] [OPTIONS]`
    *   **Description**: Ingests a user-edited report to refine generation parameters.
    *   **Source**: `src/pygramattic_reports/cli/feedback_cmd.py`

### Context & Constraints

#### Input Specifications
*   **Supported Formats**: `JSON`, `CSV`, `XLS`, `XLSX`, `DOCX`, `TXT`, `MD`.
*   **External Sources**: Google Docs, Sheets, Slides (requires auth), PostgreSQL.
*   **Schema**: All inputs are normalized to a strict JSON schema before processing.

#### Output Specifications
*   **Document Formats**: `MD`, `DOCX`, `TXT`, `HTML`.
*   **Data Formats**: `JSON`, `CSV`, `SQL`.
*   **Media Formats**: `PNG`, `JPEG`, `AVIF`, `WebP`.

#### Data Directory Structure
The system enforces a strict directory hierarchy rooted at `data/`:
*   `data/raw/`: Original ingested files.
*   `data/processed/`: Normalized JSON datasets.
*   `data/derived/`: Intermediate transformation results.
*   `data/reports/`: Final generated report artifacts.
*   `data/media/`: Generated charts and images.

#### Technical Constraints
*   **Runtime**: Python 3.11+.
*   **Core Libraries**: `pydantic` (validation), `pandas` (processing), `typer` (CLI).
*   **Linting**: Strict `ruff` configuration (see `pyproject.toml`).
*   **Type Safety**: `mypy` strict mode enforced.
