# Code Coverage

We strive for high test coverage (>80%) on core business logic.

## Coverage Tools
*   `pytest-cov`: Measures gathering coverage.
*   `coverage.py`: The underlying engine.

## Generating Report

```bash
pytest --cov=src/pygramattic_reports --cov-report=term-missing tests/
```

## Current Status (Estimated)

| Module | Coverage | Notes |
| :--- | :---: | :--- |
| `models` | 95% | Data objects are simple and well-tested. |
| `processors` | 90% | Core logic for filtering/joins is covered. |
| `templates` | 85% | Jinja2 logic is mostly standard. |
| `charts` | 70% | Visual output is harder to test; relying on snapshots. |
| `loaders` | 60% | Integration dependent; often mocked. |
| `cli` | 50% | Integration tests cover main paths, but edge cases remain. |

## Critical Gaps
*   **Charts**: Need more snapshot tests for complex chart types (sankey, waterfall).
*   **Outputs**: PowerPoint and Excel adapters have basic coverage but need edge case handling checking.
