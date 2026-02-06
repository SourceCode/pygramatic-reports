# Installation Guide

## Prerequisites

*   **Python**: Version 3.11 or higher.
*   **Package Manager**: `pip` (standard) or `hatch` (for development).
*   **Operating System**: Linux, macOS, or Windows.

## Installation Methods

### Method 1: PyPI (Recommended for Users)

```bash
pip install pygramattic-reports
```

### Method 2: Source (Recommended for Developers)

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/pygramattic-reports.git
    cd pygramattic-reports
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # on Windows: .venv\Scripts\activate
    ```

3.  **Install in editable mode**:
    ```bash
    pip install -e ".[dev,all]"
    ```
    This installs:
    *   **Core**: `pydantic`, `pandas`, `jinja2`, `typer`
    *   **Vis**: `matplotlib`, `seaborn`
    *   **IO**: `openpyxl`, `python-docx`
    *   **Dev**: `pytest`, `ruff`, `mypy`, `pre-commit`

## Verifying Installation

Verify that the CLI is accessible:

```bash
report --version
```

You should see output similar to:
`pygramattic-reports version 0.1.0`

## Common Issues

### H3: Missing Build Tools
If you encounter errors related to building wheels, ensure you have basic build tools installed:
```bash
pip install --upgrade pip setuptools wheel
```

### H3: Matplotlib Backend
On headless servers (CI/CD), you may need to configure the Matplotlib backend to `Agg` to prevent display errors:
```bash
export MPLBACKEND=Agg
```
