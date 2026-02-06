# Setup & Configuration

## Environment Variables

Pygramattic Reports uses environment variables for sensitive configuration and global settings. Create a `.env` file in your project root or set these variables in your shell.

| Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `PYGRAMATTIC_ENV` | No | `development` | Runtime environment (`development`, `production`). |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `DATA_DIR` | No | `./data` | Base directory for storing raw and processed data. |
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes (for Google) | - | Path to Google Service Account JSON key key. |
| `DB_CONNECTION_STRING` | Yes (for SQL) | - | PostgreSQL connection string (e.g., `postgresql://user:pass@localhost:5432/db`). |

## Configuration Files

The primary configuration is handled via YAML files that define report structure, data sources, and themes.

### `config.yaml` Example

```yaml
project:
  name: "Quarterly Analysis"
  version: "1.0.0"

inputs:
  - type: "csv"
    path: "data/raw/sales_q1.csv"
  - type: "google_sheet"
    id: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"

output:
  format: "markdown"
  template: "executive_summary"
  theme: "corporate_dark"
```

## Secrets Management

> [!WARNING]
> NEVER commit `.env` files or credentials to version control.

*   Use `.env.example` as a template for required variables but keep actual values in `.env`.
*   The `.gitignore` file is pre-configured to exclude `.env` and `*.key`.
*   For Google Integrations, ensure your `service-account.json` is also git-ignored.

## Data Directory Setup

The application expects a standardized directory structure, which can be initialized via CLI:

```bash
report init
```

This creates:
*   `data/raw/`: Place your input files here.
*   `data/processed/`: System-generated normalized files.
*   `data/reports/`: Generated output location.
