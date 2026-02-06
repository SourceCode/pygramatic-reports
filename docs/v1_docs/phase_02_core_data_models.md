# Phase 02: Core Data Models & Type System

## Objective

Define all shared Pydantic models that serve as the inter-module contracts. These types are the single most critical architectural element -- every module produces or consumes them, and without them, no module can be implemented or tested in isolation.

## Why This Phase Is Second

The product review identified the absence of data model definitions as the number one gap in the PRD. The types `RawData`, `Dataset`, `Report`, `Manifest`, `ChartSpec`, `TemplateSpec`, `ThemeSpec`, and `ValidationReport` are referenced throughout the PRD but never defined. This phase creates them.

## Tasks

### Task 2.1: Create Base Model Utilities

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/models/base.py`

**Description:** Create a base Pydantic model with common configuration that all models inherit from.

**Requirements:**
- Strict mode enabled (no implicit type coercion)
- Frozen models by default (immutability for safety)
- JSON serialization support
- UUID generation utility
- Timestamp generation utility

**Example:**
```python
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, ConfigDict


class PygramatticModel(BaseModel):
    """Base model for all pygramattic-reports data structures."""
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        ser_json_timedelta="iso8601",
        ser_json_bytes="base64",
    )


def generate_id() -> str:
    """Generate a unique identifier."""
    return str(uuid4())


def now_utc() -> datetime:
    """Generate a UTC timestamp."""
    return datetime.now(timezone.utc)
```

---

### Task 2.2: Define Source Configuration Models

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/models/sources.py`

**Description:** Define typed configuration for each input source type.

**Models to define:**

```python
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict


class SourceType(str, Enum):
    """Supported input source types."""
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    GDOC = "gdoc"
    GSHEET = "gsheet"
    GSLIDES = "gslides"
    POSTGRESQL = "postgresql"


class FileSourceConfig(BaseModel):
    """Configuration for file-based sources."""
    path: Path
    encoding: str = "utf-8"
    # Format-specific options
    sheet_name: str | None = None       # XLSX: which sheet to read
    delimiter: str = ","                 # CSV: field delimiter
    has_header: bool = True             # CSV/XLSX: first row is header


class DatabaseSourceConfig(BaseModel):
    """Configuration for PostgreSQL source."""
    host: str
    port: int = 5432
    database: str
    schema_name: str = "public"
    query: str | None = None            # Custom SQL query
    table: str | None = None            # Or just specify a table name
    username: str | None = None         # Can also come from env vars
    password: str | None = None         # Can also come from env vars


class GoogleSourceConfig(BaseModel):
    """Configuration for Google Workspace sources."""
    document_id: str                    # Google document/spreadsheet/presentation ID
    credentials_path: Path | None = None
    sheet_name: str | None = None       # For Google Sheets: specific sheet


class SourceConfig(BaseModel):
    """Unified source configuration."""
    source_type: SourceType
    name: str                           # Human-readable name for this source
    file: FileSourceConfig | None = None
    database: DatabaseSourceConfig | None = None
    google: GoogleSourceConfig | None = None
```

---

### Task 2.3: Define RawData Model

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/models/raw_data.py`

**Description:** Define the `RawData` type -- the output of Loaders, input to Normalizers.

**Models to define:**

```python
from datetime import datetime
from enum import Enum

from .base import PygramatticModel, generate_id, now_utc
from .sources import SourceConfig


class ContentType(str, Enum):
    """Type of content contained in raw data."""
    TABULAR = "tabular"       # CSV, XLSX, database results, Google Sheets
    DOCUMENT = "document"     # DOCX, TXT, MD, Google Docs
    PRESENTATION = "presentation"  # Google Slides


class RawData(PygramatticModel):
    """Output of a Loader. Contains unprocessed data in its original form.

    This is the bridge between input-specific loading and format-agnostic
    normalization. Loaders produce RawData; Normalizers consume it.
    """
    id: str                              # Unique identifier
    source_config: SourceConfig          # Where this data came from
    content_type: ContentType            # What kind of data this is

    # The actual content -- varies by content type:
    # - TABULAR: list of dicts (rows), or list of lists with headers separate
    # - DOCUMENT: list of text blocks (paragraphs, sections)
    # - PRESENTATION: list of slide content dicts
    tabular_data: list[dict] | None = None
    tabular_headers: list[str] | None = None
    document_text: list[str] | None = None

    # Metadata
    row_count: int | None = None
    loaded_at: datetime
    source_checksum: str | None = None   # SHA-256 of the source file
```

---

### Task 2.4: Define Dataset Model (Central Data Structure)

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/models/dataset.py`

**Description:** Define the `Dataset` type -- the central data structure that flows through processors, builders, charts, validators, and converters. This is the most important model in the system.

**Note:** `Dataset` wraps a pandas DataFrame but is not itself a DataFrame. It carries metadata, schema, and provenance alongside the data.

**Models to define:**

```python
from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, model_validator

from .base import generate_id, now_utc


class DataType(str, Enum):
    """Supported column data types (from PRD: string, int, float, date, boolean)."""
    STRING = "string"
    INTEGER = "int"
    FLOAT = "float"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"


class ColumnSchema(BaseModel):
    """Schema for a single column in a Dataset."""
    model_config = ConfigDict(frozen=True)

    name: str
    dtype: DataType
    nullable: bool = True
    description: str | None = None


class Provenance(BaseModel):
    """Tracks where a dataset came from."""
    model_config = ConfigDict(frozen=True)

    source_type: str               # e.g., "csv", "postgresql"
    source_path: str | None = None # File path or connection string
    source_name: str               # Human-readable source name
    loaded_at: datetime
    normalized_at: datetime
    row_count_raw: int             # Row count before normalization
    transformations: list[str] = []  # List of transformations applied


class Dataset:
    """The central data structure in pygramattic-reports.

    Wraps a pandas DataFrame with typed schema, provenance tracking,
    and metadata. This is NOT a Pydantic model because it holds a
    DataFrame, which is not natively serializable.

    Output of Normalizer. Input to Processors, Converters, Charts, Builder.

    Usage:
        dataset = Dataset(
            id="...",
            name="revenue_by_region",
            schema=[ColumnSchema(name="region", dtype=DataType.STRING), ...],
            dataframe=df,
            provenance=Provenance(...),
        )
        # Access data
        dataset.dataframe  # pandas DataFrame
        dataset.schema     # list[ColumnSchema]
        dataset.row_count  # int
    """

    def __init__(
        self,
        id: str,
        name: str,
        schema: list[ColumnSchema],
        dataframe: pd.DataFrame,
        provenance: Provenance,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.name = name
        self.schema = schema
        self.dataframe = dataframe
        self.provenance = provenance
        self.created_at = created_at or now_utc()

    @property
    def row_count(self) -> int:
        return len(self.dataframe)

    @property
    def column_names(self) -> list[str]:
        return [col.name for col in self.schema]

    def to_metadata_dict(self) -> dict:
        """Serialize metadata (without the DataFrame) for manifest storage."""
        return {
            "id": self.id,
            "name": self.name,
            "schema": [col.model_dump() for col in self.schema],
            "row_count": self.row_count,
            "provenance": self.provenance.model_dump(),
            "created_at": self.created_at.isoformat(),
        }
```

---

### Task 2.5: Define Report Models

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/models/report.py`

**Description:** Define the `Report` type -- the abstract report structure output by the Builder, consumed by Output Adapters.

**Models to define:**

```python
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from .base import generate_id, now_utc


class SectionType(str, Enum):
    """Types of report sections."""
    TITLE = "title"
    SUMMARY = "summary"
    NARRATIVE = "narrative"
    DATA_TABLE = "data_table"
    CHART = "chart"
    IMAGE = "image"
    HEADING = "heading"
    SPACER = "spacer"
    PAGE_BREAK = "page_break"
    TABLE_OF_CONTENTS = "table_of_contents"


class ReportSection(BaseModel):
    """A single section of a rendered report.

    The Builder produces these. Output Adapters consume them.
    The `content` field holds different data depending on `section_type`:
    - TITLE/HEADING/NARRATIVE/SUMMARY: str (text content)
    - DATA_TABLE: dict with 'headers' and 'rows' keys
    - CHART/IMAGE: bytes (image data) + media_type
    - SPACER/PAGE_BREAK: None (structural markers)
    """
    model_config = ConfigDict(frozen=True)

    section_type: SectionType
    title: str | None = None            # Section heading (if applicable)
    content: str | None = None          # Text content
    table_data: dict | None = None      # For DATA_TABLE: {"headers": [...], "rows": [[...]]}
    media_bytes: bytes | None = None    # For CHART/IMAGE: raw image data
    media_type: str | None = None       # e.g., "image/png", "image/svg+xml"
    media_path: str | None = None       # Path to saved media file
    level: int = 1                      # Heading level (1-6)
    metadata: dict = {}                 # Additional section-specific metadata


class NumberClaim(BaseModel):
    """A numerical value in the report that can be validated against source data.

    The Builder emits these during assembly so the Validator can check them
    without re-parsing the output document.
    """
    model_config = ConfigDict(frozen=True)

    section_index: int          # Which section contains this claim
    value: float                # The numeric value
    formatted_value: str        # How it appears in the report (e.g., "$1,234")
    source_dataset_id: str      # Which dataset it came from
    source_column: str          # Which column
    computation: str            # How it was derived (e.g., "sum", "avg", "raw[3]")
    description: str            # Human-readable description


class Report(BaseModel):
    """A fully assembled report, ready for output formatting.

    This is the output of the Builder and the input to Output Adapters.
    It is format-agnostic -- it describes what the report contains, not
    how it is rendered in any specific format.
    """
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    sections: list[ReportSection]
    number_claims: list[NumberClaim] = []     # For validation
    datasets_used: list[str] = []             # Dataset IDs
    template_name: str
    theme_name: str
    build_timestamp: datetime
    build_warnings: list[str] = []            # Non-fatal issues during build
```

---

### Task 2.6: Define Chart Specification Model

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/models/chart_spec.py`

**Description:** Define the abstract chart specification that decouples chart definition from rendering library.

**Models to define:**

```python
from enum import Enum

from pydantic import BaseModel, ConfigDict


class ChartType(str, Enum):
    """Supported chart types."""
    BAR = "bar"
    HORIZONTAL_BAR = "horizontal_bar"
    STACKED_BAR = "stacked_bar"
    LINE = "line"
    AREA = "area"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    BOX = "box"


class ChartRenderer(str, Enum):
    """Available chart rendering backends."""
    MATPLOTLIB = "matplotlib"
    PLOTLY = "plotly"


class ChartFormat(str, Enum):
    """Chart output image formats."""
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"


class ChartSpec(BaseModel):
    """Abstract specification for a chart.

    This model describes WHAT chart to produce, not HOW to render it.
    The Chart Engine takes a ChartSpec + Dataset + ThemeSpec and produces
    image bytes.
    """
    model_config = ConfigDict(frozen=True)

    chart_type: ChartType
    title: str
    x_column: str
    y_columns: list[str]
    dataset_id: str                              # Reference to a Dataset

    # Optional configuration
    x_label: str | None = None                   # Defaults to x_column name
    y_label: str | None = None                   # Defaults to y_columns[0] if single
    legend: bool = True
    legend_position: str = "best"

    # Sizing
    width: int = 800                             # Pixels
    height: int = 600                            # Pixels
    dpi: int = 150

    # Rendering
    renderer: ChartRenderer = ChartRenderer.MATPLOTLIB
    output_format: ChartFormat = ChartFormat.PNG

    # Data options
    sort_by: str | None = None                   # Column to sort data by
    limit: int | None = None                     # Max data points to show
    group_by: str | None = None                  # Grouping column for stacked/grouped charts

    # Theme overrides (applied on top of the report theme)
    color_override: list[str] | None = None
    background_color: str | None = None
```

---

### Task 2.7: Define Template and Theme Specification Models

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/models/template_spec.py`

**Description:** Define the typed models for template and theme YAML files.

**Models to define:**

```python
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict


# --- Template Models ---

class SectionSource(str, Enum):
    """Where section content comes from."""
    STATIC = "static"            # Content is in the template
    DATA = "data"                # Content comes from a dataset
    AI_GENERATED = "ai_generated"  # Content is generated by Claude CLI
    CHART = "chart"              # Content is a rendered chart


class TemplateSectionSpec(BaseModel):
    """Specification for a single section in a template."""
    model_config = ConfigDict(frozen=True)

    type: str                    # Section type: title, summary, narrative, data_table, chart, etc.
    source: SectionSource = SectionSource.STATIC
    content: str | None = None   # Static content or Jinja2 template string

    # For data-driven sections
    dataset: str | None = None   # Dataset name reference
    columns: list[str] | None = None  # Which columns to include

    # For chart sections
    chart_type: str | None = None
    x_column: str | None = None
    y_columns: list[str] | None = None

    # For AI-generated sections
    ai_prompt: str | None = None
    ai_max_words: int | None = None
    ai_context: str | None = None  # Additional context for the AI

    # Structural
    title: str | None = None
    level: int = 2               # Heading level
    condition: str | None = None  # Jinja2 condition for conditional rendering


class TemplateSpec(BaseModel):
    """Full template specification loaded from YAML."""
    model_config = ConfigDict(frozen=True)

    name: str
    description: str | None = None
    version: str = "1.0"
    sections: list[TemplateSectionSpec]


# --- Theme Models ---

class FontSpec(BaseModel):
    """Font configuration."""
    model_config = ConfigDict(frozen=True)

    heading: str = "Arial"
    body: str = "Calibri"
    monospace: str = "Courier New"
    size_title: int = 24
    size_heading: int = 16
    size_body: int = 11
    size_caption: int = 9


class ColorSpec(BaseModel):
    """Color palette configuration."""
    model_config = ConfigDict(frozen=True)

    primary: str = "#1a5276"
    secondary: str = "#2e86c1"
    accent: str = "#e74c3c"
    background: str = "#ffffff"
    text: str = "#2c3e50"
    text_light: str = "#7f8c8d"
    chart_palette: list[str] = [
        "#1a5276", "#2e86c1", "#85c1e9", "#e74c3c",
        "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c",
    ]


class SpacingSpec(BaseModel):
    """Spacing and layout configuration."""
    model_config = ConfigDict(frozen=True)

    section_gap_pt: int = 18
    paragraph_gap_pt: int = 6
    page_margin_inches: float = 1.0


class ChartThemeSpec(BaseModel):
    """Chart-specific theme configuration."""
    model_config = ConfigDict(frozen=True)

    background_color: str = "#ffffff"
    grid: bool = True
    grid_color: str = "#e0e0e0"
    grid_alpha: float = 0.5
    title_size: int = 14
    label_size: int = 11
    tick_size: int = 9
    legend_size: int = 10
    line_width: float = 2.0


class ThemeSpec(BaseModel):
    """Full theme specification loaded from YAML."""
    model_config = ConfigDict(frozen=True)

    name: str
    description: str | None = None
    fonts: FontSpec = FontSpec()
    colors: ColorSpec = ColorSpec()
    spacing: SpacingSpec = SpacingSpec()
    chart: ChartThemeSpec = ChartThemeSpec()
```

---

### Task 2.8: Define Validation Result Model

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/models/validation.py`

**Description:** Define the output model for the Validator.

```python
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from .base import now_utc


class CheckStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


class ValidationCheck(BaseModel):
    """A single validation check result."""
    model_config = ConfigDict(frozen=True)

    check_name: str
    status: CheckStatus
    message: str
    expected: str | None = None
    actual: str | None = None
    section_index: int | None = None     # Which report section
    severity: str = "error"              # "error", "warning", "info"


class ValidationResult(BaseModel):
    """Complete validation report."""
    model_config = ConfigDict(frozen=True)

    report_id: str
    overall_status: CheckStatus
    checks: list[ValidationCheck]
    total_checks: int
    passed: int
    failed: int
    warnings: int
    validated_at: datetime
```

---

### Task 2.9: Define Manifest Model

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/models/manifest.py`

**Description:** Define the `Manifest` model for dataset metadata stored by the Storage Manager.

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .dataset import ColumnSchema


class Manifest(BaseModel):
    """Metadata file stored alongside each dataset in the storage system.

    Persisted as `manifest.json` in each dataset's directory.
    """
    model_config = ConfigDict(frozen=True)

    id: str                              # Dataset ID
    name: str                            # Human-readable name
    source_type: str                     # Original source type
    source_path: str | None = None       # Original file path or connection info
    schema: list[ColumnSchema]           # Column definitions
    row_count: int
    checksum: str | None = None          # SHA-256 of the data file
    created_at: datetime
    storage_path: str                    # Relative path within data directory
    format: str = "parquet"              # Storage format (parquet, csv, json)
    size_bytes: int | None = None        # File size on disk
    tags: list[str] = []                 # User-defined tags
```

---

### Task 2.10: Create Models Package `__init__.py` with Re-exports

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/models/__init__.py`

**Description:** Re-export all models for convenient importing.

```python
"""Core data models for pygramattic-reports.

All inter-module contracts are defined here. Import models from this
package rather than from individual files.

Usage:
    from pygramattic_reports.models import Dataset, Report, ChartSpec
"""

from .base import PygramatticModel, generate_id, now_utc
from .chart_spec import ChartFormat, ChartRenderer, ChartSpec, ChartType
from .dataset import ColumnSchema, DataType, Dataset, Provenance
from .manifest import Manifest
from .raw_data import ContentType, RawData
from .report import NumberClaim, Report, ReportSection, SectionType
from .sources import (
    DatabaseSourceConfig,
    FileSourceConfig,
    GoogleSourceConfig,
    SourceConfig,
    SourceType,
)
from .template_spec import (
    ChartThemeSpec,
    ColorSpec,
    FontSpec,
    SectionSource,
    SpacingSpec,
    TemplateSectionSpec,
    TemplateSpec,
    ThemeSpec,
)
from .validation import CheckStatus, ValidationCheck, ValidationResult

__all__ = [
    # Base
    "PygramatticModel", "generate_id", "now_utc",
    # Sources
    "SourceType", "FileSourceConfig", "DatabaseSourceConfig",
    "GoogleSourceConfig", "SourceConfig",
    # Raw Data
    "ContentType", "RawData",
    # Dataset
    "DataType", "ColumnSchema", "Provenance", "Dataset",
    # Report
    "SectionType", "ReportSection", "NumberClaim", "Report",
    # Charts
    "ChartType", "ChartRenderer", "ChartFormat", "ChartSpec",
    # Templates & Themes
    "SectionSource", "TemplateSectionSpec", "TemplateSpec",
    "FontSpec", "ColorSpec", "SpacingSpec", "ChartThemeSpec", "ThemeSpec",
    # Validation
    "CheckStatus", "ValidationCheck", "ValidationResult",
    # Manifest
    "Manifest",
]
```

---

### Task 2.11: Write Unit Tests for All Models

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_models.py`

**Requirements:**
- Test that each model can be constructed with valid data
- Test that each model rejects invalid data (e.g., wrong types, missing required fields)
- Test serialization to/from JSON for Pydantic models
- Test `Dataset.to_metadata_dict()` produces correct output
- Test `generate_id()` returns unique strings
- Test `now_utc()` returns timezone-aware datetime

**Example test:**
```python
import pandas as pd
import pytest
from pygramattic_reports.models import (
    ColumnSchema, DataType, Dataset, Provenance, now_utc, generate_id,
    SourceConfig, SourceType, FileSourceConfig,
    ChartSpec, ChartType,
)
from pathlib import Path


def test_column_schema_creation():
    col = ColumnSchema(name="revenue", dtype=DataType.FLOAT, nullable=False)
    assert col.name == "revenue"
    assert col.dtype == DataType.FLOAT
    assert col.nullable is False


def test_dataset_creation():
    df = pd.DataFrame({"name": ["A", "B"], "value": [1, 2]})
    ds = Dataset(
        id=generate_id(),
        name="test",
        schema=[
            ColumnSchema(name="name", dtype=DataType.STRING),
            ColumnSchema(name="value", dtype=DataType.INTEGER),
        ],
        dataframe=df,
        provenance=Provenance(
            source_type="csv",
            source_path="/tmp/test.csv",
            source_name="test source",
            loaded_at=now_utc(),
            normalized_at=now_utc(),
            row_count_raw=2,
        ),
    )
    assert ds.row_count == 2
    assert ds.column_names == ["name", "value"]


def test_dataset_metadata_roundtrip():
    # Test that to_metadata_dict() produces valid JSON-serializable output
    ...


def test_chart_spec_defaults():
    spec = ChartSpec(
        chart_type=ChartType.BAR,
        title="Revenue by Region",
        x_column="region",
        y_columns=["revenue"],
        dataset_id="some-uuid",
    )
    assert spec.width == 800
    assert spec.height == 600
    assert spec.renderer.value == "matplotlib"
```

---

## Dependencies

- **Depends on:** Phase 01 (project scaffold, dependencies installed)
- **Blocks:** Phase 03 (config), Phase 04 (errors), Phase 05 (storage), Phase 06 (loaders), and every subsequent phase

## Acceptance Criteria

1. All model files exist in `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/models/`
2. All models can be imported from `pygramattic_reports.models`
3. All unit tests pass
4. `mypy` passes on all model files with no errors
5. Models correctly serialize to/from JSON (where applicable)
6. `Dataset` correctly wraps a pandas DataFrame with metadata

## References

- PRD Core Modules: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 260-365)
- PRD Data Conversion types: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 59-68)
- PRD Chart Standards: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 162-176)
