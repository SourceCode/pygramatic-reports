# Phase 06: CSV & JSON Loaders with Normalizers

## Objective

Implement the first two data ingestion paths: CSV and JSON. This includes the loader base class, format-specific loaders, the normalizer base class, and format-specific normalizers. These form the first complete vertical slice from file input to `Dataset` output.

## Why This Phase Is Sixth

With models, config, logging, errors, and storage in place, we can now build the first end-to-end data path. CSV and JSON are the simplest, most common formats and serve as the template for all future loaders.

## Tasks

### Task 6.1: Define the Loader Base Class

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/loaders/base.py`

**Description:** Abstract base class that all format-specific loaders must implement.

```python
from abc import ABC, abstractmethod
from pygramattic_reports.models import RawData, SourceConfig


class BaseLoader(ABC):
    """Abstract base class for data loaders.

    Each loader reads a specific input format and produces a RawData object.
    Loaders do NOT interpret or transform data -- they only read it.

    Subclasses must implement:
        - `load(config) -> RawData`
        - `supported_types() -> list[str]`
    """

    @abstractmethod
    def load(self, config: SourceConfig) -> RawData:
        """Load data from the configured source.

        Args:
            config: Source configuration with path, options, etc.

        Returns:
            RawData with the raw content loaded from the source.

        Raises:
            LoaderError: If the source cannot be read.
        """
        ...

    @abstractmethod
    def supported_types(self) -> list[str]:
        """Return the list of SourceType values this loader handles."""
        ...
```

---

### Task 6.2: Implement the Loader Registry

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/loaders/registry.py`

**Description:** Registry pattern for mapping source types to loader implementations.

```python
from pygramattic_reports.models import SourceType
from pygramattic_reports.exceptions import LoaderError
from .base import BaseLoader


class LoaderRegistry:
    """Registry of loader implementations.

    Usage:
        registry = LoaderRegistry()
        registry.register(CsvLoader())
        registry.register(JsonLoader())

        loader = registry.get_loader(SourceType.CSV)
        raw_data = loader.load(source_config)
    """

    def __init__(self):
        self._loaders: dict[str, BaseLoader] = {}

    def register(self, loader: BaseLoader) -> None:
        """Register a loader for its supported types."""
        for source_type in loader.supported_types():
            self._loaders[source_type] = loader

    def get_loader(self, source_type: SourceType) -> BaseLoader:
        """Get the loader for a given source type.

        Raises:
            LoaderError: If no loader is registered for this type.
        """
        loader = self._loaders.get(source_type.value)
        if loader is None:
            raise LoaderError(
                f"No loader registered for source type: {source_type.value}",
                source_type=source_type.value,
            )
        return loader

    def available_types(self) -> list[str]:
        """List all registered source types."""
        return list(self._loaders.keys())
```

---

### Task 6.3: Implement the CSV Loader

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/loaders/csv_loader.py`

**Description:** Loader for CSV files. Handles encoding detection, delimiter configuration, and header detection.

**Requirements:**
- Read CSV using Python's `csv` module (not pandas -- loaders produce raw data, not DataFrames)
- Respect `FileSourceConfig.delimiter` and `FileSourceConfig.has_header`
- Respect `FileSourceConfig.encoding` (default: UTF-8)
- Compute SHA-256 checksum of the source file
- Return `RawData` with `content_type=ContentType.TABULAR`
- Handle errors: file not found, encoding errors, malformed CSV
- Log loading progress via `get_logger("loaders.csv")`

**Example usage:**
```python
loader = CsvLoader()
config = SourceConfig(
    source_type=SourceType.CSV,
    name="sales_data",
    file=FileSourceConfig(path=Path("data/sales.csv")),
)
raw = loader.load(config)
# raw.tabular_headers == ["region", "revenue", "quarter"]
# raw.tabular_data == [{"region": "US", "revenue": "1000", "quarter": "Q1"}, ...]
# raw.row_count == 150
```

---

### Task 6.4: Implement the JSON Loader

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/loaders/json_loader.py`

**Description:** Loader for JSON files. Handles both array-of-objects (tabular) and nested document formats.

**Requirements:**
- Detect whether JSON is tabular (array of flat objects) or document (nested structure)
- For tabular JSON: extract headers from object keys, populate `tabular_data` and `tabular_headers`
- For document JSON: store entire structure for document-type processing
- Handle large files: use `json.load()` for normal files; for files > configurable threshold, consider `ijson` for streaming (but standard `json` is acceptable for V1)
- Compute SHA-256 checksum
- Return `RawData` with appropriate `content_type`
- Handle errors: file not found, invalid JSON, encoding errors

**JSON detection logic:**
```python
# Tabular: top-level is a list of dicts with consistent keys
# [{"name": "A", "value": 1}, {"name": "B", "value": 2}]

# Document: anything else (nested objects, mixed types, etc.)
# {"title": "Report", "sections": [...]}
```

---

### Task 6.5: Define the Normalizer Base Class

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/normalizers/base.py`

```python
from abc import ABC, abstractmethod
from pygramattic_reports.models import RawData, Dataset


class BaseNormalizer(ABC):
    """Abstract base class for data normalizers.

    Normalizers convert RawData (raw loaded content) into typed Dataset objects.
    This is where schema inference, type coercion, and data cleanup happen.
    """

    @abstractmethod
    def normalize(self, raw_data: RawData) -> Dataset:
        """Normalize raw data into a typed Dataset.

        This involves:
        1. Inferring column types (string, int, float, date, boolean)
        2. Coercing values to inferred types
        3. Building the schema (list of ColumnSchema)
        4. Creating the pandas DataFrame
        5. Recording provenance

        Args:
            raw_data: Raw loaded data from a Loader.

        Returns:
            A typed, validated Dataset.

        Raises:
            NormalizationError: If data cannot be normalized.
        """
        ...
```

---

### Task 6.6: Implement the Tabular Normalizer

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/normalizers/tabular.py`

**Description:** Normalizes tabular raw data (from CSV, JSON arrays, XLSX, etc.) into a typed Dataset. This is the most important normalizer -- it handles all row/column data.

**Requirements:**
- **Schema inference:** For each column, analyze all values to infer the best DataType:
  - If all values are integers (or empty): `DataType.INTEGER`
  - If all values are numbers (some with decimals): `DataType.FLOAT`
  - If values match date patterns (ISO 8601, common date formats): `DataType.DATE`
  - If values are "true"/"false"/"0"/"1": `DataType.BOOLEAN`
  - Otherwise: `DataType.STRING`
- **Type coercion:** Convert string values from the raw data to their inferred types
- **Null handling:** Empty strings, "null", "None", "N/A" should be treated as null
- **Create DataFrame:** Build a pandas DataFrame with correctly typed columns
- **Build schema:** Generate `ColumnSchema` objects for each column

**Schema inference approach:**
```python
def infer_column_type(values: list[str | None]) -> DataType:
    """Infer the data type for a column based on its values.

    Strategy: try to parse as each type in order of specificity.
    Most specific wins (boolean > integer > float > date > string).

    Non-null values are tested. If all parse successfully as a type, that type wins.
    If any value fails, try the next type.
    """
    ...
```

**Example:**
```python
normalizer = TabularNormalizer()
dataset = normalizer.normalize(raw_data)
# dataset.schema == [
#     ColumnSchema(name="region", dtype=DataType.STRING),
#     ColumnSchema(name="revenue", dtype=DataType.FLOAT),
#     ColumnSchema(name="date", dtype=DataType.DATE),
# ]
# dataset.dataframe is a typed pandas DataFrame
```

---

### Task 6.7: Create Package Inits

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/loaders/__init__.py`
```python
"""Data loaders for reading files and databases.

Usage:
    from pygramattic_reports.loaders import LoaderRegistry, CsvLoader, JsonLoader

    registry = LoaderRegistry()
    registry.register(CsvLoader())
    registry.register(JsonLoader())
"""
from .registry import LoaderRegistry
from .csv_loader import CsvLoader
from .json_loader import JsonLoader

__all__ = ["LoaderRegistry", "CsvLoader", "JsonLoader"]
```

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/normalizers/__init__.py`
```python
"""Data normalizers for converting raw data to typed Datasets.

Usage:
    from pygramattic_reports.normalizers import TabularNormalizer

    normalizer = TabularNormalizer()
    dataset = normalizer.normalize(raw_data)
"""
from .tabular import TabularNormalizer

__all__ = ["TabularNormalizer"]
```

---

### Task 6.8: Create Test Fixtures

**Files to create:**
- `/Volumes/SecondDrive/code2/pygramattic-reports/tests/fixtures/sample.csv`
- `/Volumes/SecondDrive/code2/pygramattic-reports/tests/fixtures/sample_tabular.json`
- `/Volumes/SecondDrive/code2/pygramattic-reports/tests/fixtures/sample_document.json`
- `/Volumes/SecondDrive/code2/pygramattic-reports/tests/fixtures/sample_types.csv` (mixed types for inference testing)

**`sample.csv`:**
```csv
region,revenue,quarter,growth_pct,is_active
US,1500.50,Q1,12.5,true
EU,2300.75,Q1,8.3,true
APAC,890.25,Q1,-2.1,false
US,1650.00,Q2,10.0,true
EU,2500.00,Q2,8.7,true
```

**`sample_tabular.json`:**
```json
[
    {"name": "Product A", "price": 29.99, "quantity": 150, "launch_date": "2024-01-15"},
    {"name": "Product B", "price": 49.99, "quantity": 75, "launch_date": "2024-03-01"},
    {"name": "Product C", "price": 19.99, "quantity": 300, "launch_date": "2024-06-10"}
]
```

---

### Task 6.9: Write Loader and Normalizer Tests

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_loaders.py`

**Test cases:**
1. `test_csv_loader_basic` -- Load sample.csv, verify headers and row count
2. `test_csv_loader_custom_delimiter` -- Load a semicolon-delimited file
3. `test_csv_loader_no_header` -- Load CSV without headers
4. `test_csv_loader_file_not_found` -- Raises `LoaderError`
5. `test_csv_loader_encoding` -- Handle UTF-8 with BOM, Latin-1
6. `test_json_loader_tabular` -- Load array-of-objects JSON
7. `test_json_loader_document` -- Load nested document JSON
8. `test_json_loader_invalid` -- Raises `LoaderError` for invalid JSON
9. `test_registry_get_loader` -- Registry returns correct loader
10. `test_registry_unknown_type` -- Registry raises `LoaderError`

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_normalizers.py`

**Test cases:**
1. `test_tabular_normalizer_csv_data` -- CSV raw data normalizes correctly
2. `test_type_inference_integer` -- Column of integers detected as INTEGER
3. `test_type_inference_float` -- Column of decimals detected as FLOAT
4. `test_type_inference_date` -- ISO date strings detected as DATE
5. `test_type_inference_boolean` -- true/false strings detected as BOOLEAN
6. `test_type_inference_mixed` -- Mixed types fall back to STRING
7. `test_null_handling` -- Empty strings treated as null
8. `test_schema_generation` -- Correct ColumnSchema list produced
9. `test_provenance_tracking` -- Dataset carries source information
10. `test_normalizer_empty_data` -- Handle empty datasets gracefully

---

## Dependencies

- **Depends on:** Phase 01-05 (scaffold, models, config, logging/errors, storage)
- **Blocks:** Phase 07 (additional loaders), Phase 08 (CLI ingest command)

## Acceptance Criteria

1. `CsvLoader` loads CSV files into `RawData` objects
2. `JsonLoader` loads JSON files into `RawData` objects (both tabular and document)
3. `TabularNormalizer` converts tabular `RawData` into typed `Dataset` objects
4. Schema inference correctly identifies string, int, float, date, boolean columns
5. `LoaderRegistry` routes source types to correct loaders
6. All error cases raise typed exceptions with clear messages
7. All tests pass

## References

- PRD Input Handling: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 36-56)
- PRD Loaders Module: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 262-270)
- PRD Normalizers Module: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 274-279)
- PRD Data Types: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (line 67)
