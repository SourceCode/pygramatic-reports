# API Reference

Pygramattic Reports provides a fluent Python API for programmatic report generation, useful for integrating into other applications (Flask/FastAPI/Django).

## `Pygramattic`

The main entry point for the fluent interface.

```python
from pygramattic_reports.api import Pygramattic

report = (
    Pygramattic()
    .configure(title="Q1 Report", author="Data Team")
    .add_dataset("sales", df_sales)  # Pass pandas DataFrame directly
    .add_dataset("targets", df_targets)
    .add_section(
        title="Executive Summary",
        content="Sales were strong this quarter...",
        type="narrative"
    )
    .add_chart(
        title="Sales vs Targets",
        dataset="sales",
        chart_type="bar",
        x="region",
        y=["amount", "target"]
    )
    .build()
)

# Export
report.save("report.html")
report.save("report.pdf")
```

## `Linker` & `Loader`

Low-level access to data ingestion.

```python
from pygramattic_reports.loaders import CsvLoader

loader = CsvLoader()
dataset = loader.load("data.csv")
print(dataset.schema)
```

## `ChartEngine`

Direct access to the charting subsystem.

```python
from pygramattic_reports.charts import ChartEngine
from pygramattic_reports.models import ChartSpec

spec = ChartSpec(chart_type="line", x_column="date", y_columns=["val"])
image_bytes = ChartEngine().generate(spec, dataset, theme)
```

## Error Handling

All custom exceptions inherit from `PygramatticError`.

*   `ConfigError`: Invalid configuration or YAML.
*   `DataError`: Missing columns, validation failures, or merge errors.
*   `BuildError`: Failures during the rendering phase.
