# Installation Guide

## Prerequisites

Before installing Pygramattic Reports, ensure you have the following:

*   **Python**: Version 3.11 or higher.
*   **Operating System**: Linux, macOS, or Windows.
*   **Git**: For cloning the repository.

## Package Manager

We recommend using `pip` or `hatch` for managing dependencies.

## Installation Steps

1.  **Clone the Repository**

    ```bash
    git clone https://github.com/yourusername/pygramattic-reports.git
    cd pygramattic-reports
    ```

2.  **Create a Virtual Environment (Optional but Recommended)**

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install Dependencies**

    Install the package in editable mode with all optional dependencies (dev, test, google):

    ```bash
    pip install -e ".[all]"
    ```

    Or install specific groups:

    ```bash
    pip install -e ".[dev]"  # For development tools
    pip install -e ".[google]" # For Google integrations
    ```

## Verify Installation

Run the CLI help command to verify the installation:

```bash
report --help
```

You should see the output:
`Pygramattic Reports - Unified Report Processing & Generation Tool`

## Common Issues

### Python Version Mismatch
If you see an error related to Python version, ensure you are running 3.11+:
```bash
python --version
```

### Dependency Conflicts
If you have existing packages that conflict, try attempting a clean install in a fresh virtual environment.
