# Security

## Authentication

### Google Services
We use **Service Account** authentication for server-to-server communication with Google APIs.
*   Keys are JSON files.
*   **NEVER** commit these keys to the repository.
*   Use `GOOGLE_APPLICATION_CREDENTIALS` env var to load them.

### Databases
Database connections typically use a Connection String containing username and password.
*   Use `DB_CONNECTION_STRING` env var.
*   Ensure your database user has "Least Privilege" (e.g., Read-Only access if only ingesting).

## Secrets Management

*   **Local Dev**: Use `.env` file (git-ignored).
*   **Production**: Use your platform's secret manager (e.g., AWS Secrets Manager, GitHub Secrets).

## Input Validation

All external input is treated as untrusted.
*   **Files**: Validated against MIME types and extension allowlists.
*   **Data**: Parsed through strict Pydantic models to prevent injection or malformed data issues.
*   **SQL**: We use parameterized queries (via SQLAlchemy/Pandas) to prevent SQL Injection.

## Dependency Security

We use `bandit` to scan our codebase for common security issues.

```bash
pip install bandit
bandit -r src/
```
