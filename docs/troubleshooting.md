# Troubleshooting

Common issues and how to resolve them.

## Common Errors

### `FileNotFoundError: [Errno 2] No such file or directory`
*   **Cause**: The input file path specified in `ingest` or `config.yaml` is incorrect.
*   **Fix**: Verify the file path is absolute or relative to your current working directory.

### `ValidationError: Field 'source' required`
*   **Cause**: The input data does not match the expected schema or is missing required columns.
*   **Fix**: Check your source file headers. Ensure normalizers are correctly mapped.

### `GoogleAuthError: Invalid Credentials`
*   **Cause**: `GOOGLE_APPLICATION_CREDENTIALS` env var is missing or points to an invalid/expired key.
*   **Fix**: Re-download your Service Account JSON key and update the environment variable.

### `TemplateNotFound: 'report.html'`
*   **Cause**: The template specified in config does not exist in `src/pygramattic_reports/templates`.
*   **Fix**: Check the template name in your config.

## Debugging

Enable verbose logging to see detailed traces:

```bash
report --verbose build ...
```

This will print stack traces and debug information to the console.

## Resetting Data

If your `data/` directory gets corrupted state, you can safely delete `data/processed` and `data/derived` and re-run ingestion.

```bash
rm -rf data/processed/* data/derived/*
report ingest ...
```
