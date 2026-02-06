# Pygramattic Reports

> Unified Python Report Processing & Generation Tool

A comprehensive, declarative reporting engine for Python that ingests data from standard sources (CSV, Excel, JSON), validates it, processes it (joins, filters, aggregates), and generates publication-quality verified reports in HTML, PDF, and PowerPoint formats.

## 🚀 Key Capabilities

*   **Declarative Templates**: Define report structure and logic in simple YAML.
*   **Data Pipeline**: Built-in filtering, joins, sorting, and aggregation (no code required).
*   **Strict Validation**: Enforce data quality rules (uniqueness, completeness) before rendering.
*   **Advanced Charts**: 15+ chart types including Waterfall, Sankey, and Gauges via Matplotlib/Seaborn.
*   **Theming**: Separate content from style with robust theme definitions (Color, Typography, CSS).
*   **Multi-Format**: Export to HTML, Markdown, and PowerPoint.

## 🏗 Architecture Summary

Pygramattic follows a linear compilation pipeline:

1.  **Loader**: Ingests raw data into Pandas DataFrames.
2.  **Builder**: Resolves the YAML template and applies the Theme.
3.  **Processor**: Executes data transformations (Joins, Filters) and Validation rules.
4.  **Renderer**: Generates visualizations and final artifacts using format adapters.

[Read the full Architecture Guide](/docs/implementation.md).

## 🛠 Tech Stack

*   **Runtime**: Python 3.11+
*   **Core**: Pydantic 2.0, Pandas 2.0, Jinja2
*   **Vis**: Matplotlib 3.7+, Seaborn
*   **CLI**: Typer, Rich
*   **Quality**: MyPy (Strict), Ruff, Pytest

## ⚡ Quick Start

### Installation

```bash
pip install pygramattic-reports
```

### Create Your First Report

```bash
# 1. Initialize project
report init my-report
cd my-report

# 2. Add data
echo "category,value\nA,10\nB,20" > data.csv

# 3. Build
report build --config config.yaml
```

See the [First Run Guide](/docs/first-run.md) for a complete walkthrough.

## 📚 Documentation Index

### Core
*   [Installation](/docs/install.md)
*   [Setup & Config](/docs/setup.md)
*   [User Guide](/docs/user_guide.md)

### Technical
*   [Functionality](/docs/functionality.md)
*   [Data Schema](/docs/schema.md)
*   [API Reference](/docs/api.md)
*   [Integrations](/docs/integrations.md)

### Ops & Quality
*   [Testing Strategy](/docs/testing.md)
*   [Code Coverage](/docs/coverage.md)
*   [Security](/docs/security.md)
*   [Troubleshooting](/docs/troubleshooting.md)

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](/docs/contributing.md) to get started.

## 📄 License

MIT License.
