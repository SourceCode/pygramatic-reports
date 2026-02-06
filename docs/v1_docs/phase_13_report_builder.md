# Phase 13: Report Builder (Core, Without AI)

## Objective

Build the core report builder that assembles reports from templates, themes, and datasets. This phase implements the full assembly pipeline WITHOUT AI-generated content (Claude CLI integration comes in Phase 17-18). Data-driven sections (tables, charts) and static sections work fully.

## Why This Phase Is Thirteenth

All upstream components are now ready: templates, themes, chart engine, data loaders, normalizers, and storage. The builder is the central orchestrator that combines everything into a report. Building it without AI first ensures the core pipeline works end-to-end.

## Tasks

### Task 13.1: Implement the Report Builder

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/builder/builder.py`

**Description:** The core report assembly engine. Takes a report configuration, loads the template and theme, resolves data bindings, generates charts and tables, and produces an abstract `Report` object.

**Interface:**

```python
from pathlib import Path
from pygramattic_reports.models import (
    Report, ReportSection, SectionType, NumberClaim,
    TemplateSpec, ThemeSpec, Dataset, TemplateSectionSpec,
    generate_id, now_utc,
)
from pygramattic_reports.charts import ChartEngine
from pygramattic_reports.templates import TemplateRenderer
from pygramattic_reports.logging import BuildLog, get_logger


class ReportBuilder:
    """Core report assembly engine.

    Takes a report configuration and assembles a Report by:
    1. Loading and resolving the template
    2. Loading the theme
    3. For each section in the template:
       a. STATIC: render the content directly
       b. DATA: build a data table from the referenced dataset
       c. CHART: generate a chart using the chart engine
       d. AI_GENERATED: placeholder (replaced in Phase 18)
    4. Collect all sections into a Report object
    5. Track number claims for validation

    Usage:
        builder = ReportBuilder(
            chart_engine=ChartEngine(),
            template_renderer=TemplateRenderer(),
        )
        report = builder.build(build_config)
    """

    def __init__(
        self,
        chart_engine: ChartEngine,
        template_renderer: TemplateRenderer,
    ):
        self.chart_engine = chart_engine
        self.template_renderer = template_renderer
        self.logger = get_logger("builder")

    def build(self, config: BuildConfig) -> tuple[Report, BuildLog]:
        """Build a report from the given configuration.

        Args:
            config: Report build configuration specifying template,
                    theme, datasets, and output preferences.

        Returns:
            Tuple of (Report, BuildLog). The Report contains all
            assembled sections. The BuildLog tracks the build process.

        Raises:
            BuildError: If the build fails fatally.
        """
        build_log = BuildLog(build_id=generate_id(), started_at=now_utc())

        # 1. Resolve template with context
        context = self._build_context(config)
        resolved_sections = self.template_renderer.resolve_template(
            config.template, context
        )

        # 2. Process each section
        report_sections = []
        number_claims = []

        for i, section_spec in enumerate(resolved_sections):
            try:
                section, claims = self._process_section(
                    section_spec, config, i
                )
                report_sections.append(section)
                number_claims.extend(claims)
                build_log.sections_generated += 1
            except Exception as e:
                if self._is_recoverable(e):
                    self.logger.warning("Section skipped", index=i, error=str(e))
                    build_log.add_entry("warning", "builder", f"Section {i} skipped: {e}")
                    build_log.sections_skipped += 1
                else:
                    raise

        # 3. Assemble the Report
        report = Report(
            id=generate_id(),
            name=config.report_name,
            sections=report_sections,
            number_claims=number_claims,
            datasets_used=[ds.id for ds in config.datasets.values()],
            template_name=config.template.name,
            theme_name=config.theme.name,
            build_timestamp=now_utc(),
            build_warnings=[e.message for e in build_log.entries if e.level == "warning"],
        )

        build_log.finalize("completed" if build_log.sections_skipped == 0 else "completed_with_warnings")
        return report, build_log
```

---

### Task 13.2: Define the Build Configuration Model

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/builder/config.py`

**Description:** The typed configuration for a report build, loaded from `report_config.yaml`.

```python
from pydantic import BaseModel
from pygramattic_reports.models import TemplateSpec, ThemeSpec, Dataset


class BuildConfig(BaseModel):
    """Configuration for a single report build.

    Loaded from a report_config.yaml file or constructed programmatically.
    """
    report_name: str
    template: TemplateSpec
    theme: ThemeSpec
    datasets: dict[str, Dataset]          # name -> Dataset mapping
    primary_dataset: str | None = None    # Name of the main dataset

    # Output preferences
    output_formats: list[str] = ["md"]
    output_directory: str = "data/reports/"

    # AI settings (used in Phase 18)
    ai_enabled: bool = False
    ai_sections: list[str] = []

    class Config:
        arbitrary_types_allowed = True    # For Dataset (not a pure Pydantic model)
```

---

### Task 13.3: Implement Section Processors

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/builder/section_processors.py`

**Description:** Processing functions for each section type. The builder dispatches to these based on `section_spec.source`.

```python
from pygramattic_reports.models import (
    ReportSection, SectionType, NumberClaim,
    TemplateSectionSpec, SectionSource, Dataset, ThemeSpec,
    ChartSpec, ChartType, ChartRenderer,
)
from pygramattic_reports.charts import ChartEngine


def process_static_section(
    spec: TemplateSectionSpec,
) -> tuple[ReportSection, list[NumberClaim]]:
    """Process a static content section (title, heading, narrative, page_break).

    Returns the ReportSection with the static content.
    """
    section_type = _map_section_type(spec.type)
    return ReportSection(
        section_type=section_type,
        title=spec.title,
        content=spec.content,
        level=spec.level,
    ), []


def process_data_table_section(
    spec: TemplateSectionSpec,
    dataset: Dataset,
) -> tuple[ReportSection, list[NumberClaim]]:
    """Process a data table section.

    Extracts the requested columns from the dataset and formats
    as a table structure (headers + rows).

    Also generates NumberClaims for any numeric values in the table,
    so the validator can check them.
    """
    # Select columns
    columns = spec.columns or dataset.column_names
    df = dataset.dataframe[columns]

    headers = list(df.columns)
    rows = df.values.tolist()

    # Generate number claims for numeric columns
    claims = []
    for col_idx, col_name in enumerate(headers):
        col_schema = next((c for c in dataset.schema if c.name == col_name), None)
        if col_schema and col_schema.dtype in ("int", "float"):
            for row_idx, row in enumerate(rows):
                claims.append(NumberClaim(
                    section_index=-1,  # Will be set by builder
                    value=float(row[col_idx]) if row[col_idx] is not None else 0,
                    formatted_value=str(row[col_idx]),
                    source_dataset_id=dataset.id,
                    source_column=col_name,
                    computation=f"raw[{row_idx}]",
                    description=f"{col_name} row {row_idx}",
                ))

    return ReportSection(
        section_type=SectionType.DATA_TABLE,
        title=spec.title,
        table_data={"headers": headers, "rows": rows},
    ), claims


def process_chart_section(
    spec: TemplateSectionSpec,
    dataset: Dataset,
    theme: ThemeSpec,
    chart_engine: ChartEngine,
) -> tuple[ReportSection, list[NumberClaim]]:
    """Process a chart section.

    Builds a ChartSpec from the template section spec, generates
    the chart using the chart engine, and returns the image bytes.
    """
    chart_spec = ChartSpec(
        chart_type=ChartType(spec.chart_type),
        title=spec.title or "Chart",
        x_column=spec.x_column,
        y_columns=spec.y_columns or [],
        dataset_id=dataset.id,
    )

    image_bytes = chart_engine.generate(chart_spec, dataset, theme)

    return ReportSection(
        section_type=SectionType.CHART,
        title=spec.title,
        media_bytes=image_bytes,
        media_type=f"image/{chart_spec.output_format.value}",
    ), []


def process_ai_placeholder_section(
    spec: TemplateSectionSpec,
) -> tuple[ReportSection, list[NumberClaim]]:
    """Placeholder for AI-generated sections (until Phase 18).

    Returns a section with a placeholder message indicating
    AI content would be generated here.
    """
    return ReportSection(
        section_type=_map_section_type(spec.type),
        title=spec.title,
        content=f"[AI-generated content placeholder: {spec.ai_prompt or 'No prompt specified'}]",
        metadata={"ai_placeholder": True, "ai_prompt": spec.ai_prompt},
    ), []
```

---

### Task 13.4: Implement the Common Function Library

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/processors/functions.py`

**Description:** Spreadsheet-like operations that can be used in templates and by the builder to compute derived values from datasets.

**Requirements (from PRD):**
- Aggregations: sum, avg, min, max, count
- Joins: merge two datasets
- Filters: filter rows by condition
- Window functions: running total, moving average
- Percent change
- Ratios

```python
import pandas as pd
from pygramattic_reports.models import Dataset


def aggregate(dataset: Dataset, column: str, operation: str) -> float:
    """Compute an aggregate over a dataset column.

    Args:
        dataset: Source dataset
        column: Column name
        operation: "sum", "avg", "min", "max", "count"

    Returns:
        Computed aggregate value
    """
    ops = {
        "sum": lambda s: s.sum(),
        "avg": lambda s: s.mean(),
        "min": lambda s: s.min(),
        "max": lambda s: s.max(),
        "count": lambda s: s.count(),
    }
    if operation not in ops:
        raise ValueError(f"Unknown operation: {operation}")
    return float(ops[operation](dataset.dataframe[column]))


def filter_rows(dataset: Dataset, column: str, operator: str, value) -> pd.DataFrame:
    """Filter dataset rows by a condition.

    Args:
        column: Column to filter on
        operator: "eq", "ne", "gt", "gte", "lt", "lte", "contains"
        value: Comparison value
    """
    ...


def percent_change(dataset: Dataset, column: str, periods: int = 1) -> pd.Series:
    """Compute percent change over periods for a column."""
    return dataset.dataframe[column].pct_change(periods=periods)


def ratio(dataset: Dataset, numerator_col: str, denominator_col: str) -> pd.Series:
    """Compute ratio of two columns."""
    return dataset.dataframe[numerator_col] / dataset.dataframe[denominator_col]


def running_total(dataset: Dataset, column: str) -> pd.Series:
    """Compute running total (cumulative sum) of a column."""
    return dataset.dataframe[column].cumsum()


def moving_average(dataset: Dataset, column: str, window: int = 3) -> pd.Series:
    """Compute moving average of a column."""
    return dataset.dataframe[column].rolling(window=window).mean()
```

---

### Task 13.5: Implement the Report Config Loader

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/builder/config_loader.py`

**Description:** Load a `report_config.yaml` file and resolve all references (template, theme, datasets) into a `BuildConfig`.

```python
from pathlib import Path
from pygramattic_reports.models import TemplateSpec, ThemeSpec
from pygramattic_reports.templates import TemplateLoader
from pygramattic_reports.themes import ThemeLoader
from pygramattic_reports.storage import StorageManager
from pygramattic_reports.config import AppConfig
from .config import BuildConfig


def load_build_config(
    config_path: Path,
    app_config: AppConfig,
    storage: StorageManager,
) -> BuildConfig:
    """Load a report_config.yaml and resolve all references.

    Resolves:
    - Template name → TemplateSpec (loaded from templates_dir)
    - Theme name → ThemeSpec (loaded from themes_dir)
    - Dataset IDs → Dataset objects (loaded from storage)

    Args:
        config_path: Path to report_config.yaml
        app_config: Application configuration
        storage: Storage manager for loading datasets

    Returns:
        Fully resolved BuildConfig

    Raises:
        BuildError: If config is invalid or references cannot be resolved.
    """
    ...
```

---

### Task 13.6: Create Builder Package Init

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/builder/__init__.py`

```python
"""Report builder for pygramattic-reports.

Assembles reports from templates, themes, and datasets.

Usage:
    from pygramattic_reports.builder import ReportBuilder, load_build_config

    config = load_build_config(Path("report_config.yaml"), app_config, storage)
    builder = ReportBuilder(chart_engine, template_renderer)
    report, build_log = builder.build(config)
"""
from .builder import ReportBuilder
from .config import BuildConfig
from .config_loader import load_build_config

__all__ = ["ReportBuilder", "BuildConfig", "load_build_config"]
```

---

### Task 13.7: Create Processors Package Init

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/processors/__init__.py`

```python
"""Data processing functions (spreadsheet-like operations).

Usage:
    from pygramattic_reports.processors import aggregate, filter_rows, percent_change
"""
from .functions import (
    aggregate, filter_rows, percent_change, ratio,
    running_total, moving_average,
)

__all__ = [
    "aggregate", "filter_rows", "percent_change", "ratio",
    "running_total", "moving_average",
]
```

---

### Task 13.8: Write Builder Tests

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_builder.py`

**Test cases:**
1. `test_build_static_sections` -- Title + heading sections render correctly
2. `test_build_data_table_section` -- Data table contains correct headers and rows
3. `test_build_chart_section` -- Chart section contains image bytes
4. `test_build_ai_placeholder` -- AI sections get placeholder content
5. `test_build_full_report` -- Complete template produces Report with all sections
6. `test_build_missing_dataset` -- Raises BuildError for missing dataset reference
7. `test_build_conditional_section_included` -- Condition=true → section included
8. `test_build_conditional_section_excluded` -- Condition=false → section excluded
9. `test_build_log_tracking` -- BuildLog records events correctly
10. `test_number_claims_generated` -- Data table sections generate NumberClaims
11. `test_build_recoverable_error` -- Chart failure skips section, continues build

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_processors.py`

**Test cases:**
1. `test_aggregate_sum` -- Sum operation
2. `test_aggregate_avg` -- Average operation
3. `test_filter_rows_eq` -- Equality filter
4. `test_percent_change` -- Percent change calculation
5. `test_ratio` -- Column ratio
6. `test_running_total` -- Cumulative sum
7. `test_moving_average` -- Moving average

---

## Dependencies

- **Depends on:** Phase 02 (Report model), Phase 05 (storage), Phase 10 (templates), Phase 11 (themes), Phase 12 (chart engine)
- **Blocks:** Phase 14 (Markdown output), Phase 15 (DOCX output), Phase 18 (AI integration), Phase 19 (validator)

## Acceptance Criteria

1. `ReportBuilder.build()` produces a `Report` with correctly assembled sections
2. Static sections render with resolved Jinja2 variables
3. Data table sections contain correct data from datasets
4. Chart sections contain valid image bytes
5. AI sections get placeholder content (until Phase 18)
6. BuildLog tracks the entire build process
7. NumberClaims are generated for numeric data
8. All tests pass

## References

- PRD Report Builder: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 108-143)
- PRD Common Function Library: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 128-136)
- PRD Processor Engine: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 304-312)
