# API Reference

## Core API

### Pygramattic (Fluent Interface)

The main entry point for programmatic report generation.

```python
from pygramattic_reports.api import Pygramattic

report = Pygramattic().configure(...).build()
```

#### Methods

- `configure(title=None, author=None, ...)`: Set report metadata.
- `add_dataset(name, data)`: Register a pandas DataFrame or list of dicts.
- `add_section(title, content, type="narrative")`: Add a text section.
- `add_chart(title, dataset, chart_type, ...)`: Add a visualization.
- `build()`: Compile the report into a `BuiltReport` object.

### Models

- `Dataset`: Wrapper for pandas DataFrames with schema metadata.
- `Report`: Abstract representation of a generated report.
- `ReportSection`: A single content block (charts, text, tables).

### Core Components

- `ReportBuilder`: Orchestrates the assembly of reports from templates and data.
- `ChartEngine`: Handles visualization rendering (Matplotlib base).
- `TemplateRenderer`: Jinja2-based text expansion.
