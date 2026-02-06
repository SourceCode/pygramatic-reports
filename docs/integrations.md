# Integrations

Pygramattic Reports supports various external integrations for data ingestion.

## Supported Integrations

| Integration | Type | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| **Google Sheets** | Source | Yes (Service Account) | Ingest tabular data from Sheets key. |
| **Google Docs** | Source | Yes (Service Account) | Ingest text architecture from Docs. |
| **PostgreSQL** | Source | Yes (Connection String) | Query data directly via SQL. |
| **Local Files** | Source | No | CSV, JSON, Excel, Word, Markdown. |

## Google Workspace Setup

To use Google integrations, you must set up a Service Account in Google Cloud Console.

1.  **Create Project**: Go to Google Cloud Console and create a new project.
2.  **Enable APIs**: Enable "Google Sheets API" and "Google Drive API".
3.  **Create Service Account**: IAM & Admin > Service Accounts > Create.
4.  **Download Key**: Create a new JSON key for the service account.
5.  **Save Key**: Save the JSON file locally (e.g., `credentials.json`).
6.  **Configure Env**: Set `GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json`.
7.  **Share Files**: Share your Google Sheets/Docs with the service account email address.

## Database Integration

To connect to a SQL database:

1.  Install the `sqlalchemy` extra: `pip install ".[sql]"` (if applicable).
2.  Set `DB_CONNECTION_STRING` in `.env`.
3.  In `config.yaml`, use the `sql` source type:

```yaml
inputs:
  - type: "sql"
    query: "SELECT * FROM monthly_sales WHERE quarter = 'Q1'"
    name: "db_sales"
```

## Local Testing

We provide Mock Loaders for testing integrations without live connections. Set `PYGRAMATTIC_ENV=test` to force the use of local fixtures instead of real API calls.
