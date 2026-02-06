# Testing Strategy

We rely on `pytest` for a comprehensive testing suite.

## Test Levels

### Unit Tests (`tests/unit/`)
*   **Focus**: Individual functions and methods.
*   **Mocking**: Heavy use of `unittest.mock` to isolate from disk and network.
*   **Speed**: Fast execution (< 2s).

### Integration Tests (`tests/integration/`)
*   **Focus**: Interaction between `Loader`, `Builder`, and `OutputAdapter`.
*   **Data**: Uses real sample files in `data/`.
*   **Goal**: Verify that a full report can be built from checking constraints.

### Snapshot Tests (`tests/snapshots/`)
*   **Tool**: `syrupy` (pytest plugin).
*   **Focus**: Visual regression for HTML and Chart output.
*   **Goal**: Ensure changes to the engine don't accidentally break layout.

## Running Tests

```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/unit

# Run with coverage (slow)
pytest --cov=src/pygramattic_reports tests/
```

## writing Tests

We use `pytest` fixtures for common setups.

```python
def test_data_processor(basic_dataset):
    processor = DataProcessor()
    result = processor.process(basic_dataset, ...)
    assert len(result) == 5
```
