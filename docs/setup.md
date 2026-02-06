# Setup & Configuration

This guide covers environment variables, configuration files, and secrets management for Pygramattic Reports.

## Environment Variables

The application uses `pydantic-settings` to load configuration from environment variables or `.env` files.

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `DATA_DIR` | No | `./data` | Default directory for looking up datasets. |
| `OUTPUT_DIR` | No | `./output` | Default directory for generated reports. |
| `THEME_DIR` | No | `./themes` | Directory for custom theme definitions (`.yaml`). |
| `TEMPLATE_DIR` | No | `./templates` | Directory for custom report templates (`.yaml`). |
| `GOOGLE_APPLICATION_CREDENTIALS` | No | - | Path to Google Service Account JSON (for Sheets/Docs ingestion). |
| `OPENAI_API_KEY` | No | - | API Key for AI-driven summaries/insights (if enabled). |
| `ANTHROPIC_API_KEY` | No | - | API Key for Claude-based AI features. |

### Example `.env` File

Create a file named `.env` in your project root:

```ini
LOG_LEVEL=DEBUG
DATA_DIR=./my_data
OUTPUT_DIR=./reports
GOOGLE_APPLICATION_CREDENTIALS=certs/google-service-account.json
```

## Configuration Files (`config.yaml`)

Reports are typically built using a run configuration file.

```yaml
# config.yaml
job_name: "monthly_sales_q1"
template: "sales_report_v1"
theme: "corporate_blue"

datasets:
  sales_data: "./data/q1_sales.csv"
  targets: "./data/targets_2023.json"

output:
  format: ["html", "pdf"]
  filename: "Q1_Sales_Report"
```

## Secrets Management

> [!WARNING]
> **NEVER commit secrets to version control.**

*   **API Keys**: Use environment variables (`OPENAI_API_KEY`).
*   **Service Accounts**: parameters pointing to file paths (like `GOOGLE_APPLICATION_CREDENTIALS`) should reference files that are listed in `.gitignore`.
*   **CI/CD**: inject these variables via GitHub Secrets or similar vault mechanisms.
