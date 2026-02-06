# Phase 01: Project Scaffold & Tooling

## Objective

Establish the foundational project structure, build tooling, dependency management, and development workflow. This phase creates the skeleton that every subsequent phase builds upon.

## Why This Phase Comes First

Every module, test, and configuration depends on a properly structured Python project. Without a `pyproject.toml`, linting rules, and directory layout, parallel development is impossible and code quality will diverge immediately.

## Tasks

### Task 1.1: Initialize Python Project with `pyproject.toml`

**Description:** Create a modern Python project configuration using `pyproject.toml` as the single source of truth for project metadata, dependencies, and tool configuration.

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/pyproject.toml`

**Requirements:**
- Project name: `pygramattic-reports`
- Python version: `>=3.11`
- Build system: `hatchling` or `setuptools`
- Include all core dependencies (see dependency list below)
- Include optional dependency groups: `[dev]`, `[test]`, `[google]`, `[all]`
- Configure `ruff` for linting and formatting
- Configure `mypy` for type checking
- Configure `pytest` for testing

**Core dependencies:**
```
pydantic>=2.0
pyyaml>=6.0
pandas>=2.0
jinja2>=3.1
typer>=0.9
rich>=13.0
matplotlib>=3.7
seaborn>=0.12
openpyxl>=3.1
python-docx>=1.0
structlog>=23.0
```

**Dev dependencies:**
```
pytest>=7.0
pytest-cov>=4.0
pytest-mock>=3.0
ruff>=0.1
mypy>=1.5
pre-commit>=3.0
```

**Optional Google dependencies:**
```
google-api-python-client>=2.0
google-auth>=2.0
google-auth-oauthlib>=1.0
```

**Example `pyproject.toml` structure:**
```toml
[project]
name = "pygramattic-reports"
version = "0.1.0"
description = "Unified Python Report Processing & Generation Tool"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0",
    "pyyaml>=6.0",
    "pandas>=2.0",
    # ... etc
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "ruff>=0.1", "mypy>=1.5", "pre-commit>=3.0"]
test = ["pytest>=7.0", "pytest-cov>=4.0", "pytest-mock>=3.0"]
google = ["google-api-python-client>=2.0", "google-auth>=2.0"]
all = ["pygramattic-reports[dev,test,google]"]

[project.scripts]
report = "pygramattic_reports.cli.main:app"

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM"]

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
```

---

### Task 1.2: Create Source Directory Structure

**Description:** Create the complete `src/` directory layout matching the PRD's repository structure, plus additions identified in the product review.

**Directories to create:**
```
/Volumes/SecondDrive/code2/pygramattic-reports/
├── src/
│   └── pygramattic_reports/
│       ├── __init__.py
│       ├── models/              # Core data models (Phase 02)
│       │   └── __init__.py
│       ├── loaders/             # File and database loaders
│       │   └── __init__.py
│       ├── normalizers/         # Raw data -> Dataset normalization
│       │   └── __init__.py
│       ├── converters/          # Dataset -> JSON/SQL conversion
│       │   └── __init__.py
│       ├── storage/             # Storage manager
│       │   └── __init__.py
│       ├── processors/          # Data transformation functions
│       │   └── __init__.py
│       ├── charts/              # Chart generation engine
│       │   └── __init__.py
│       ├── templates/           # Template engine
│       │   └── __init__.py
│       ├── themes/              # Theme engine
│       │   └── __init__.py
│       ├── builder/             # Report builder
│       │   └── __init__.py
│       ├── validator/           # Report validator
│       │   └── __init__.py
│       ├── feedback/            # Feedback tool
│       │   └── __init__.py
│       ├── outputs/             # Output format adapters
│       │   └── __init__.py
│       ├── ai/                  # Claude CLI integration
│       │   └── __init__.py
│       ├── cli/                 # CLI interface
│       │   └── __init__.py
│       ├── config/              # Configuration management
│       │   └── __init__.py
│       └── logging/             # Logging setup
│           └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── fixtures/                # Test data files
│   ├── unit/
│   │   └── __init__.py
│   └── integration/
│       └── __init__.py
├── configs/
│   └── default.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   ├── derived/
│   ├── reports/
│   └── media/
├── docs/
│   ├── PRD.md
│   └── v1_docs/
└── sample_templates/
    └── .gitkeep
```

**Each `__init__.py` should contain:** A module-level docstring describing the package's purpose.

**Example:**
```python
# src/pygramattic_reports/loaders/__init__.py
"""Loaders for reading data from files and databases.

Each loader reads a specific format and returns RawData objects
for downstream normalization.
"""
```

---

### Task 1.3: Create `.gitignore`

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/.gitignore`

**Must include:**
```
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/
*.egg
.mypy_cache/
.ruff_cache/
.pytest_cache/
.coverage
htmlcov/
venv/
.venv/
.env
*.log
data/raw/*
data/processed/*
data/derived/*
data/reports/*
data/media/*
!data/**/.gitkeep
```

---

### Task 1.4: Create `.gitkeep` Files for Empty Directories

**Description:** Git does not track empty directories. Add `.gitkeep` files to preserve the `data/` directory structure.

**Files to create:**
- `/Volumes/SecondDrive/code2/pygramattic-reports/data/raw/.gitkeep`
- `/Volumes/SecondDrive/code2/pygramattic-reports/data/processed/.gitkeep`
- `/Volumes/SecondDrive/code2/pygramattic-reports/data/derived/.gitkeep`
- `/Volumes/SecondDrive/code2/pygramattic-reports/data/reports/.gitkeep`
- `/Volumes/SecondDrive/code2/pygramattic-reports/data/media/.gitkeep`

---

### Task 1.5: Create `conftest.py` with Base Fixtures

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/conftest.py`

**Requirements:**
- Fixture for a temporary data directory (using `tmp_path`)
- Fixture for a sample configuration object
- Fixture for a sample CSV string/file

**Example:**
```python
import pytest
from pathlib import Path


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory structure."""
    for subdir in ["raw", "processed", "derived", "reports", "media"]:
        (tmp_path / subdir).mkdir()
    return tmp_path


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    """Create a sample CSV file for testing."""
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("name,value,date\nAlpha,100,2024-01-01\nBeta,200,2024-01-02\n")
    return csv_path
```

---

### Task 1.6: Verify Project Installation

**Description:** Ensure the project can be installed in development mode.

**Commands to run:**
```bash
cd /Volumes/SecondDrive/code2/pygramattic-reports
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,test]"
pytest tests/ -v  # Should discover 0 tests, no errors
ruff check src/
mypy src/pygramattic_reports/
```

**Acceptance criteria:**
- `pip install -e ".[dev,test]"` completes without errors
- `pytest` runs without errors (0 tests collected is fine)
- `ruff check` passes with no violations
- `mypy` passes with no errors
- `report --help` shows the CLI entrypoint (even if it just says "No commands defined yet")

---

## Dependencies

- **Depends on:** Nothing (this is Phase 01)
- **Blocks:** Every subsequent phase

## Acceptance Criteria

1. `pyproject.toml` exists and is valid
2. All source directories exist with `__init__.py` files
3. All data directories exist with `.gitkeep` files
4. `.gitignore` properly excludes build artifacts and data files
5. Project installs in dev mode without errors
6. `ruff`, `mypy`, and `pytest` all run without errors
7. The `report` CLI entrypoint is registered

## References

- PRD Repository Structure: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 239-255)
- PRD Quality Attributes: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 220-225)
