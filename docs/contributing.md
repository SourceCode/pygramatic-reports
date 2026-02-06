# Contributing Guide

Thank you for your interest in contributing to Pygramattic Reports!

## Workflow

1.  **Fork** the repository.
2.  **Create a Branch** for your feature or fix (`git checkout -b feature/amazing-feature`).
3.  **Install Dev Dependencies** (`pip install -e ".[dev]"`).
4.  **Write Code**.
5.  **Write Tests** (verify with `pytest`).
6.  **Lint** (verify with `ruff check .`).
7.  **Push** to your fork.
8.  **Open a Pull Request**.

## Code Style

We follow strict coding standards:

*   **Formatter**: `black` (via Ruff)
*   **Linter**: `ruff`
*   **Type Checker**: `mypy` (Strict mode)

Run the full quality suite before committing:

```bash
ruff check .
mypy .
pytest
```

## Commit Messages

Please usage conventional commits:
*   `feat: add new csv loader`
*   `fix: resolve normalization error`
*   `docs: update readme`

## Pull Request Process

*   Ensure CI passes.
*   Update documentation if you change functionality.
*   Add a description of your changes in the PR.
