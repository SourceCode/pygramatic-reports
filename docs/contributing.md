# Contributing Guide

## Development Workflow

1.  **Fork & Clone**: Standard GitHub flow.
2.  **Environment**: Use `hatch` or `venv` to set up dependencies.
3.  **Branching**: Use feature branches `feature/my-feature`.
4.  **Commits**: Use conventional commits (e.g., `feat: add new chart type`).

## Standards

### Code Style
We use **Ruff** for linting and formatting. It is strict.

```bash
# Check code
ruff check src/

# Format code
ruff format src/
```

### Type Safety
We use **MyPy** in strict mode. All public functions must have type hints.

```bash
mypy src/
```

### Testing
New features must include unit tests. New bug fixes must include a regression test.

## Review Process

1.  Open a PR targeting `main`.
2.  Ensure CI passes (Lint + Test).
3.  A maintainer will review. Focus is on API consistency and Test Coverage.
