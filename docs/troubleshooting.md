# Troubleshooting

## Common Errors

### 1. `FileNotFoundError` during ingestion
*   **Cause**: The path in `config.yaml` is relative to where you ran the command, not the config file.
*   **Fix**: Use absolute paths or be mindful of your current working directory (CWD).

### 2. `TemplateNotFound`
*   **Cause**: The value in `template: "my_template"` does not match any file in `templates/my_template.yaml`.
*   **Fix**: Check the `TEMPLATE_DIR` env var and file extensions.

### 3. "Matplotlib display" errors
*   **Cause**: Running on a server without an X11 window system.
*   **Fix**: `export MPLBACKEND=Agg`

### 4. "Data Validation Error"
*   **Cause**: Your data failed strict validation rules (e.g., uniqueness, non-null).
*   **Fix**: Clean your input data or relax the validation rules in the template section.

## Debugging

Use the detailed logging to trace execution:

```bash
LOG_LEVEL=DEBUG report build ...
```

This will print which files are loaded, which template sections are being processed, and the shape of the dataframes at each step.

## Resetting State

The application is largely stateless. If you suspect caching issues:
1.  Clear the `__pycache__` directories.
2.  (Future) Clear any local `./.cache` folders if configured.
