# Pygramattic Reports User Guide

Pygramattic Reports is a declarative reporting engine for Python that converts data and templates into beautiful PDF, Markdown, HTML, and PowerPoint reports.

## Getting Started

### Installation

```bash
pip install pygramattic-reports
```

### Basic Usage (Fluent API)

The easiest way to create a report is using the `Pygramattic` fluent API.

```python
import pandas as pd
from pygramattic_reports.api import Pygramattic

# 1. Prepare your data
df = pd.DataFrame({
    "Product": ["Widget A", "Widget B", "Widget C"],
    "Sales": [100, 150, 80],
    "Region": ["North", "North", "South"]
})

# 2. Build the report
report = (
    Pygramattic()
    .configure(title="Quarterly Sales", author="Data Team")
    .add_dataset("sales", df)
    .add_section("Executive Summary", "Sales output was strong in Q1.")
    .add_chart(
        title="Sales by Product",
        dataset="sales",
        chart_type="bar",
        x_col="Product",
        y_cols=["Sales"]
    )
    .build()
)

# 3. Save output
report.save("sales_report.html")
report.save("sales_report.md")
```

## Creating Templates

Templates are defined in YAML. They separate content structure from code.

`reports/my_template.yaml`:
```yaml
name: "Sales Template"
sections:
  - title: "Overview"
    type: "narrative"
    content: "Overview of {{ dataset.name }}"
  
  - title: "Sales Data"
    type: "data_table"
    dataset: "sales"
    columns: ["Product", "Sales"]

  - title: "Performance"
    type: "chart"
    dataset: "sales"
    chart_type: "bar"
    x_column: "Product"
    y_columns: ["Sales"]
```

## Theming

Pygramattic supports extensive theming to match your brand. Themes are also YAML files.

`themes/brand.yaml`:
```yaml
colors:
  primary: "#0052cc"
  secondary: "#ff9900"
  background: "#ffffff"
  text: "#333333"

typography:
  font_family: "Helvetica, Arial, sans-serif"
  base_font_size: 12
  heading_font_size: 24

chart:
  palette: ["#0052cc", "#ff9900", "#6554c0"]
  show_grid: true
```

## Advanced Features

### Lazy Loading
For large datasets, use `LazyDataset` to defer loading until the report is actually built.

```python
from pygramattic_reports.core.lazy import LazyDataset
from pygramattic_reports.api import Pygramattic

def load_large_data():
    print("Loading data...")
    return pd.read_csv("huge_file.csv"), [], None

lazy_ds = LazyDataset(id="big_data", name="Big Data", loader=load_large_data)

# Uses lazy_ds...
```

### Caching
The engine automatically caches chart rendering and data processing. To configure caching behavior, use the environment variables:
- `PYGRAMATTIC_CACHE__ENABLED=true`
- `PYGRAMATTIC_CACHE__DIR=/tmp/cache`

### Parallel Rendering
Chart generation utilizes multiple cores by default.
