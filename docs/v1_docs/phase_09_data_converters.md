# Phase 09: Data Converters

## Objective

Implement the data conversion module that transforms `Dataset` objects to JSON and SQL formats. This includes schema-aware serialization and SQL DDL generation.

## Why This Phase Is Ninth

Converters are independent of the report-building pipeline but are essential for data export workflows (`report export`). They also feed into the output system later. Building them now rounds out the data pipeline before moving to report assembly.

## Tasks

### Task 9.1: Implement the JSON Converter

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/converters/json_converter.py`

**Description:** Convert a `Dataset` to JSON format with type-aware serialization.

**Requirements:**
- Support two JSON layouts:
  1. **Records** (default): `[{"col1": val, "col2": val}, ...]` -- array of objects
  2. **Columnar**: `{"col1": [val, ...], "col2": [val, ...]}` -- object of arrays
- Handle type serialization:
  - `DataType.DATE` → ISO 8601 string (`"2024-01-15"`)
  - `DataType.DATETIME` → ISO 8601 with time (`"2024-01-15T10:30:00"`)
  - `DataType.FLOAT` → JSON number (not string)
  - `DataType.INTEGER` → JSON integer
  - `DataType.BOOLEAN` → JSON boolean
  - `null` / `NaN` → JSON `null`
- Support pretty-printing (indented) and compact mode
- Deterministic output: keys sorted, consistent formatting

**Interface:**
```python
from pygramattic_reports.models import Dataset


def to_json(
    dataset: Dataset,
    layout: str = "records",       # "records" or "columnar"
    indent: int | None = 2,        # None for compact
    sort_keys: bool = True,
) -> str:
    """Convert a Dataset to a JSON string.

    Args:
        dataset: The source dataset
        layout: Output structure ("records" or "columnar")
        indent: JSON indentation (None for compact)
        sort_keys: Sort object keys alphabetically

    Returns:
        JSON string representation of the dataset

    Raises:
        ConversionError: If serialization fails
    """
    ...
```

---

### Task 9.2: Implement the SQL Converter

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/converters/sql_converter.py`

**Description:** Convert a `Dataset` to SQL DDL (CREATE TABLE) and DML (INSERT statements).

**Requirements:**
- Generate `CREATE TABLE` statement with correct SQL types:
  - `DataType.STRING` → `TEXT` (PostgreSQL) / `TEXT` (SQLite)
  - `DataType.INTEGER` → `INTEGER`
  - `DataType.FLOAT` → `DOUBLE PRECISION` (PostgreSQL) / `REAL` (SQLite)
  - `DataType.DATE` → `DATE`
  - `DataType.DATETIME` → `TIMESTAMP`
  - `DataType.BOOLEAN` → `BOOLEAN`
- Generate `INSERT INTO` statements for all rows
- Support SQL dialects: PostgreSQL (default), SQLite
- Table name: derived from `dataset.name` (sanitized for SQL identifiers)
- Handle SQL injection prevention: use parameterized-style quoting for string values
- Handle NULL values correctly
- Support `DROP TABLE IF EXISTS` prefix (optional)
- Deterministic output: consistent ordering

**Interface:**
```python
from pygramattic_reports.models import Dataset


def to_sql(
    dataset: Dataset,
    dialect: str = "postgresql",   # "postgresql" or "sqlite"
    table_name: str | None = None, # Override table name (default: dataset.name)
    drop_existing: bool = False,
    batch_size: int = 100,         # Number of rows per INSERT statement
) -> str:
    """Convert a Dataset to SQL DDL + INSERT statements.

    Args:
        dataset: The source dataset
        dialect: SQL dialect ("postgresql" or "sqlite")
        table_name: Override table name
        drop_existing: Include DROP TABLE IF EXISTS
        batch_size: Rows per INSERT statement

    Returns:
        SQL string with CREATE TABLE and INSERT statements

    Raises:
        ConversionError: If conversion fails
    """
    ...
```

**Example output:**
```sql
CREATE TABLE revenue_by_region (
    region TEXT NOT NULL,
    revenue DOUBLE PRECISION,
    quarter TEXT NOT NULL,
    is_active BOOLEAN
);

INSERT INTO revenue_by_region (region, revenue, quarter, is_active) VALUES
    ('US', 1500.50, 'Q1', TRUE),
    ('EU', 2300.75, 'Q1', TRUE),
    ('APAC', 890.25, 'Q1', FALSE);
```

---

### Task 9.3: Implement the CSV Converter

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/converters/csv_converter.py`

**Description:** Convert a `Dataset` back to CSV format.

**Requirements:**
- Use Python's `csv` module for proper quoting and escaping
- Configurable delimiter (default: comma)
- Include header row
- Handle special characters in values (newlines, commas, quotes)
- Deterministic output

**Interface:**
```python
def to_csv(
    dataset: Dataset,
    delimiter: str = ",",
    include_header: bool = True,
) -> str:
    """Convert a Dataset to CSV format."""
    ...
```

---

### Task 9.4: Create Converters Package Init

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/converters/__init__.py`

```python
"""Data format converters.

Convert Dataset objects to various output formats.

Usage:
    from pygramattic_reports.converters import to_json, to_sql, to_csv

    json_str = to_json(dataset)
    sql_str = to_sql(dataset, dialect="postgresql")
    csv_str = to_csv(dataset)
"""
from .json_converter import to_json
from .sql_converter import to_sql
from .csv_converter import to_csv

__all__ = ["to_json", "to_sql", "to_csv"]
```

---

### Task 9.5: Write Converter Tests

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_converters.py`

**Test cases:**

**JSON converter:**
1. `test_to_json_records_layout` -- Default layout produces array of objects
2. `test_to_json_columnar_layout` -- Columnar layout produces object of arrays
3. `test_to_json_date_serialization` -- Dates serialized as ISO 8601
4. `test_to_json_null_handling` -- NaN/None serialized as null
5. `test_to_json_deterministic` -- Same input always produces same output
6. `test_to_json_compact` -- No indentation when indent=None

**SQL converter:**
7. `test_to_sql_postgresql` -- Correct DDL for PostgreSQL types
8. `test_to_sql_sqlite` -- Correct DDL for SQLite types
9. `test_to_sql_with_drop` -- Includes DROP TABLE IF EXISTS
10. `test_to_sql_null_values` -- NULL handled correctly in INSERTs
11. `test_to_sql_string_escaping` -- Single quotes escaped properly
12. `test_to_sql_table_name_sanitization` -- Invalid chars removed from name
13. `test_to_sql_batch_inserts` -- Large datasets split into batches

**CSV converter:**
14. `test_to_csv_basic` -- Standard CSV output
15. `test_to_csv_custom_delimiter` -- Semicolon delimiter
16. `test_to_csv_special_characters` -- Values with commas, quotes, newlines

---

## Dependencies

- **Depends on:** Phase 02 (Dataset model), Phase 04 (ConversionError)
- **Blocks:** Phase 16 (CLI export command)

## Acceptance Criteria

1. `to_json()` produces valid, deterministic JSON from any Dataset
2. `to_sql()` produces valid DDL + INSERT statements for PostgreSQL and SQLite
3. `to_csv()` produces valid CSV with proper escaping
4. Type serialization is correct for all DataType values
5. All tests pass

## References

- PRD Data Conversion: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 59-68)
- PRD Converters Module: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 282-289)
- PRD Output Formats (Structured): `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 198-201)
