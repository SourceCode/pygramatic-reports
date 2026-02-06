# Security & Authentication

## Authentication Model

Pygramattic Reports is primarily a CLI tools designed to run in a trusted environment (local dev or secure CI/CD).

*   **No User Accounts**: There is no internal user database.
*   **Filesystem Access**: The tool has read/write access to whatever the running user allows.

## Secrets Handling

*   **API Keys**: Never pass API keys as CLI arguments. Use Environment variables (`OPENAI_API_KEY`).
*   **Credentials**: Google Service Account keys should be kept in a secure, git-ignored directory.

## Dependency Security

We use `bandit` to scan for common python security issues and `safety` to check for CVEs in dependencies.

```bash
# Run security check
bandit -r src/
safety check
```

## Output Safety

*   **HTML Escaping**: The Jinja2 environment is configured with `autoescape=True` to prevent XSS if un-sanitized data is rendered into HTML reports.
*   **Path Traversal**: Loaders validate input paths to ensure they don't break out of allowed directories (basic checks only; run in sandboxed env if handling untrusted user input).
