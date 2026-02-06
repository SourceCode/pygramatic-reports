# Architecture & Implementation

## Repository Structure

The codebase is organized as a standard Python package structure.

```text
src/
  pygramattic_reports/
    __init__.py
    cli/            # Typer CLI commands
    config/         # Configuration loading logic
    loaders/        # Input adapters (CSV, Google, etc.)
    models/         # Pydantic data models
    normalizers/    # Data standardization logic
    processors/     # Pandas data transformation
    storage/        # Filesystem management
    templates/      # Jinja2 template engine
    validator/      # Logic for validating outputs
```

## Key Design Patterns

### 1. Adapter Pattern (Loaders)
We use a registry-based Adapter pattern for Loaders. All loaders inherit from `BaseLoader` and must implement `load(source) -> RawData`. New loaders can be registered at runtime.

### 2. Pipeline Pattern (Build Process)
The build process is a linear pipeline. Data flows through a series of distinct stages, each transforming the input into a more refined state. This ensures testability of each stage in isolation.

```python
# Conceptual Flow
pipeline = Pipeline([
    LoaderStage(),
    NormalizerStage(),
    ProcessorStage(),
    RendererStage()
])
pipeline.run(config)
```

### 3. Repository Pattern (Storage)
The `storage` module abstracts physical file system access. This allows swapping local storage for S3 or other cloud storage solutions in the future without changing core logic.

## State Management

The application is largely stateless.
*   **Config**: Loaded at startup.
*   **Data**: Passed explicitly between functions.
*   **State Persistence**: Handled via file system artifacts in `data/` (intermediate files serve as checkpoints).

## Observability

We use `structlog` for structured JSON logging.
*   **Logs**: Written to `stdout` (CLI) and optional log files.
*   **Levels**: `INFO` for standard operations, `DEBUG` for detailed trace data.

## Deployment

The application is designed to be deployed as a Docker container or a standalone CLI tool.
*   **Docker**: A `Dockerfile` is provided for containerized execution.
*   **CI/CD**: GitHub Actions workflow builds wheels and runs tests on push.
