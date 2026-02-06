# Testing Strategy

We employ a comprehensive testing strategy using `pytest`.

## Test Structure

Tests are located in the `tests/` directory:

*   `tests/unit/`: Fast, isolated tests for individual functions and classes. logic.
*   `tests/integration/`: Tests that verify interactions between modules (e.g., Loader -> Normalizer).
*   `tests/fixtures/`: Reusable test data and Pytest fixtures.

## Running Tests

### Unit Tests
Run unit tests to verify logic in isolation:

```bash
pytest tests/unit
```

### Integration Tests
Run integration tests to verify component interaction:

```bash
pytest tests/integration
```

### Full Suite
Run all tests:

```bash
pytest
```

## Test Data
We use fixtures defined in `tests/conftest.py` and `tests/fixtures/` to provide specific data inputs (mock CSVs, JSONs) to tests.

## Continuous Integration
Tests are automatically run on every Pull Request via GitHub Actions. Merging to `main` is blocked if tests fail.
