# Code Coverage

We strive for high test coverage to ensure system stability and reliability.

## Coverage Tools

We use `pytest-cov` to generate coverage reports.

## Running Coverage

To generate a coverage report locally:

```bash
pytest --cov=src/pygramattic_reports tests/
```

To generate an HTML report (useful for identifying gaps):

```bash
pytest --cov=src/pygramattic_reports --cov-report=html tests/
open htmlcov/index.html
```

## Coverage Thresholds

We enforce a minimum coverage threshold of **80%**. The build will fail if coverage drops below this metric.

## Current Status (Estimated)

| Module | Statements | Branches | Functions | Status |
| :--- | :--- | :--- | :--- | :--- |
| `loaders` | 90% | 85% | 95% | ✅ Strong |
| `normalizers` | 85% | 80% | 90% | ✅ Strong |
| `processors` | 75% | 70% | 80% | ⚠️ Needs Improvement |
| `templates` | 80% | 75% | 85% | ✅ Stable |
| **Total** | **~82%** | **~78%** | **~88%** | **PASSING** |

## Improvement Plan
*   Add more edge-case tests for `processors`.
*   Increase integration test coverage for complex report building scenarios.
