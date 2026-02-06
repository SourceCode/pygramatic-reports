# Phase 12: Chart Engine (Matplotlib + Seaborn)

## Objective

Build the chart generation engine with a library-agnostic interface and the Matplotlib/Seaborn renderer. Charts accept an abstract `ChartSpec`, apply theme styling, and produce image bytes.

## Why This Phase Is Twelfth

The Report Builder (Phase 13) needs to generate charts for chart-type sections. The chart engine must be functional before the builder can produce visual reports. Matplotlib is the primary renderer; Plotly support can be added later.

## Tasks

### Task 12.1: Define the Chart Renderer Interface

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/charts/base.py`

**Description:** Abstract base class that all chart renderers implement. This decouples chart specification from rendering library.

```python
from abc import ABC, abstractmethod
import pandas as pd
from pygramattic_reports.models import ChartSpec, ThemeSpec


class BaseChartRenderer(ABC):
    """Abstract chart renderer.

    Takes a ChartSpec (what to draw), a DataFrame (the data),
    and a ThemeSpec (how it should look), and produces image bytes.

    Implementations exist for matplotlib and plotly.
    """

    @abstractmethod
    def render(
        self,
        spec: ChartSpec,
        data: pd.DataFrame,
        theme: ThemeSpec,
    ) -> bytes:
        """Render a chart to image bytes.

        Args:
            spec: What chart to render (type, columns, title, etc.)
            data: The data to visualize
            theme: Visual styling to apply

        Returns:
            Image bytes in the format specified by spec.output_format

        Raises:
            ChartError: If rendering fails
        """
        ...

    @abstractmethod
    def supported_chart_types(self) -> list[str]:
        """List chart types this renderer supports."""
        ...
```

---

### Task 12.2: Implement the Matplotlib Renderer

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/charts/matplotlib_renderer.py`

**Description:** Full Matplotlib + Seaborn chart renderer supporting all standard chart types.

**Requirements:**
- Support all `ChartType` values: bar, horizontal_bar, stacked_bar, line, area, pie, donut, scatter, heatmap, box
- Apply theme styling via `ThemeApplicator.to_matplotlib_params()`
- Use the Agg backend for headless rendering (no display required)
- Clear titles, labeled axes (always -- per PRD)
- Apply chart palette from theme
- Deterministic rendering: set random seed, use Agg backend, pin font
- Output as PNG, SVG, or PDF via `savefig()`
- Return image bytes (not file path)
- Handle edge cases: empty data, single data point, very long labels

**Implementation structure:**

```python
import io
import matplotlib
matplotlib.use("Agg")  # Must be before pyplot import
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pygramattic_reports.models import ChartSpec, ChartType, ThemeSpec
from pygramattic_reports.themes import ThemeApplicator
from pygramattic_reports.exceptions import ChartError


class MatplotlibRenderer(BaseChartRenderer):

    def render(self, spec: ChartSpec, data: pd.DataFrame, theme: ThemeSpec) -> bytes:
        """Render chart using matplotlib/seaborn."""
        # 1. Apply theme
        applicator = ThemeApplicator(theme)
        plt.rcParams.update(applicator.to_matplotlib_params())
        palette = applicator.get_chart_palette()

        # 2. Create figure
        fig, ax = plt.subplots(
            figsize=(spec.width / spec.dpi, spec.height / spec.dpi),
            dpi=spec.dpi,
        )

        # 3. Dispatch to chart-type-specific method
        try:
            self._render_chart(spec, data, ax, palette)
        except Exception as e:
            plt.close(fig)
            raise ChartError(f"Failed to render {spec.chart_type.value} chart: {e}", chart_type=spec.chart_type.value)

        # 4. Apply common styling
        ax.set_title(spec.title, fontsize=theme.chart.title_size, pad=12)
        ax.set_xlabel(spec.x_label or spec.x_column, fontsize=theme.chart.label_size)
        if spec.y_label:
            ax.set_ylabel(spec.y_label, fontsize=theme.chart.label_size)
        elif len(spec.y_columns) == 1:
            ax.set_ylabel(spec.y_columns[0], fontsize=theme.chart.label_size)

        if spec.legend and len(spec.y_columns) > 1:
            ax.legend(loc=spec.legend_position)

        plt.tight_layout()

        # 5. Export to bytes
        buf = io.BytesIO()
        fig.savefig(buf, format=spec.output_format.value, dpi=spec.dpi, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def _render_chart(self, spec, data, ax, palette):
        """Dispatch to chart-type-specific rendering."""
        renderers = {
            ChartType.BAR: self._render_bar,
            ChartType.HORIZONTAL_BAR: self._render_horizontal_bar,
            ChartType.STACKED_BAR: self._render_stacked_bar,
            ChartType.LINE: self._render_line,
            ChartType.AREA: self._render_area,
            ChartType.PIE: self._render_pie,
            ChartType.DONUT: self._render_donut,
            ChartType.SCATTER: self._render_scatter,
            ChartType.HEATMAP: self._render_heatmap,
            ChartType.BOX: self._render_box,
        }
        render_fn = renderers.get(spec.chart_type)
        if render_fn is None:
            raise ChartError(f"Unsupported chart type: {spec.chart_type.value}")
        render_fn(spec, data, ax, palette)

    def _render_bar(self, spec, data, ax, palette):
        """Render a vertical bar chart."""
        ...

    def _render_horizontal_bar(self, spec, data, ax, palette):
        """Render a horizontal bar chart."""
        ...

    def _render_stacked_bar(self, spec, data, ax, palette):
        """Render a stacked bar chart."""
        ...

    def _render_line(self, spec, data, ax, palette):
        """Render a line chart."""
        ...

    def _render_area(self, spec, data, ax, palette):
        """Render an area chart."""
        ...

    def _render_pie(self, spec, data, ax, palette):
        """Render a pie chart."""
        ...

    def _render_donut(self, spec, data, ax, palette):
        """Render a donut chart (pie with center hole)."""
        ...

    def _render_scatter(self, spec, data, ax, palette):
        """Render a scatter plot."""
        ...

    def _render_heatmap(self, spec, data, ax, palette):
        """Render a heatmap using seaborn."""
        ...

    def _render_box(self, spec, data, ax, palette):
        """Render a box plot using seaborn."""
        ...

    def supported_chart_types(self) -> list[str]:
        return [ct.value for ct in ChartType]
```

---

### Task 12.3: Implement the Chart Engine (Orchestrator)

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/charts/engine.py`

**Description:** High-level chart engine that routes chart specs to the appropriate renderer and manages chart generation.

```python
from pygramattic_reports.models import ChartSpec, ChartRenderer, Dataset, ThemeSpec
from pygramattic_reports.exceptions import ChartError
from .base import BaseChartRenderer
from .matplotlib_renderer import MatplotlibRenderer


class ChartEngine:
    """High-level chart generation engine.

    Routes ChartSpec to the appropriate renderer, handles data extraction
    from Datasets, and manages the rendering pipeline.

    Usage:
        engine = ChartEngine()
        chart_bytes = engine.generate(spec, dataset, theme)
    """

    def __init__(self):
        self._renderers: dict[str, BaseChartRenderer] = {
            "matplotlib": MatplotlibRenderer(),
        }

    def register_renderer(self, name: str, renderer: BaseChartRenderer) -> None:
        """Register an additional renderer (e.g., plotly)."""
        self._renderers[name] = renderer

    def generate(
        self,
        spec: ChartSpec,
        dataset: Dataset,
        theme: ThemeSpec,
    ) -> bytes:
        """Generate a chart from a spec and dataset.

        Args:
            spec: Chart specification
            dataset: Source data
            theme: Visual styling

        Returns:
            Image bytes

        Raises:
            ChartError: If rendering fails
        """
        # 1. Get renderer
        renderer = self._renderers.get(spec.renderer.value)
        if renderer is None:
            raise ChartError(f"Renderer not available: {spec.renderer.value}")

        # 2. Extract relevant data from dataset
        data = self._extract_data(spec, dataset)

        # 3. Render
        return renderer.render(spec, data, theme)

    def _extract_data(self, spec: ChartSpec, dataset: Dataset):
        """Extract the columns needed for the chart from the dataset.

        Validates that required columns exist. Applies optional
        sorting and limiting.
        """
        required_cols = [spec.x_column] + spec.y_columns
        if spec.group_by:
            required_cols.append(spec.group_by)

        missing = [c for c in required_cols if c not in dataset.dataframe.columns]
        if missing:
            raise ChartError(
                f"Columns not found in dataset '{dataset.name}': {missing}",
                chart_type=spec.chart_type.value,
            )

        data = dataset.dataframe[required_cols].copy()

        if spec.sort_by and spec.sort_by in data.columns:
            data = data.sort_values(spec.sort_by)

        if spec.limit:
            data = data.head(spec.limit)

        return data
```

---

### Task 12.4: Create Charts Package Init

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/charts/__init__.py`

```python
"""Chart and graph generation engine.

Supports matplotlib/seaborn rendering with theme-aware styling.

Usage:
    from pygramattic_reports.charts import ChartEngine

    engine = ChartEngine()
    image_bytes = engine.generate(chart_spec, dataset, theme)
"""
from .engine import ChartEngine
from .matplotlib_renderer import MatplotlibRenderer

__all__ = ["ChartEngine", "MatplotlibRenderer"]
```

---

### Task 12.5: Write Chart Engine Tests

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_charts.py`

**Test cases:**

1. `test_bar_chart_renders` -- Bar chart produces non-empty PNG bytes
2. `test_line_chart_renders` -- Line chart renders successfully
3. `test_pie_chart_renders` -- Pie chart renders successfully
4. `test_scatter_chart_renders` -- Scatter plot renders successfully
5. `test_chart_applies_theme` -- Theme colors affect output (check file is produced, different themes produce different byte sizes)
6. `test_chart_missing_column` -- Raises `ChartError` for missing column
7. `test_chart_empty_data` -- Handles empty DataFrame gracefully
8. `test_chart_single_point` -- Handles single data point
9. `test_chart_svg_output` -- SVG format produces valid output
10. `test_chart_with_sorting` -- Data sorting is applied
11. `test_chart_with_limit` -- Data limiting is applied
12. `test_chart_deterministic` -- Same input produces same output bytes

**Note on deterministic testing:** PNG bytes may vary slightly across runs due to floating point rendering. Use image comparison with a tolerance or check only for structural properties (file size within range, valid PNG header, etc.).

**Example:**
```python
import pandas as pd
from pygramattic_reports.charts import ChartEngine
from pygramattic_reports.models import (
    ChartSpec, ChartType, Dataset, ColumnSchema, DataType,
    ThemeSpec, Provenance, generate_id, now_utc,
)


@pytest.fixture
def sample_dataset():
    df = pd.DataFrame({
        "region": ["US", "EU", "APAC", "LATAM"],
        "revenue": [1500, 2300, 890, 650],
    })
    return Dataset(
        id=generate_id(), name="test",
        schema=[
            ColumnSchema(name="region", dtype=DataType.STRING),
            ColumnSchema(name="revenue", dtype=DataType.INTEGER),
        ],
        dataframe=df,
        provenance=Provenance(
            source_type="test", source_name="test",
            loaded_at=now_utc(), normalized_at=now_utc(), row_count_raw=4,
        ),
    )


def test_bar_chart_renders(sample_dataset):
    engine = ChartEngine()
    spec = ChartSpec(
        chart_type=ChartType.BAR,
        title="Revenue by Region",
        x_column="region",
        y_columns=["revenue"],
        dataset_id=sample_dataset.id,
    )
    result = engine.generate(spec, sample_dataset, ThemeSpec(name="test"))
    assert len(result) > 0
    assert result[:8] == b"\x89PNG\r\n\x1a\n"  # Valid PNG header
```

---

## Dependencies

- **Depends on:** Phase 02 (ChartSpec, ThemeSpec models), Phase 04 (ChartError), Phase 11 (ThemeApplicator)
- **Blocks:** Phase 13 (builder generates charts)

## Acceptance Criteria

1. `ChartEngine.generate()` produces valid PNG images for all chart types
2. SVG and PDF output formats work
3. Theme styling is applied to charts (colors, fonts, grid)
4. Missing columns raise `ChartError`
5. Edge cases handled: empty data, single point, long labels
6. All tests pass

## References

- PRD Chart & Graph Generator: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 162-176)
- PRD Chart Engine Module: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 316-325)
- PRD Chart Standards: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 171-175)
