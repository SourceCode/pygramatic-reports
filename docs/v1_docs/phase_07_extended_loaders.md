# Phase 07: XLSX, DOCX, TXT, and Markdown Loaders

## Objective

Extend the loader system with support for Excel workbooks (XLSX), Word documents (DOCX), plain text files (TXT), and Markdown files (MD). This covers all V1 file-based input formats.

## Why This Phase Is Seventh

With the loader architecture established in Phase 06 (base class, registry, normalizer), adding new formats follows the same pattern. Each new loader registers itself and produces `RawData` for the existing normalizer pipeline.

## Tasks

### Task 7.1: Implement the XLSX Loader

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/loaders/xlsx_loader.py`

**Description:** Load Excel workbooks using `openpyxl`. Handles multi-sheet workbooks, merged cells, and date formatting.

**Requirements:**
- Use `openpyxl` to read `.xlsx` and `.xls` files
- Respect `FileSourceConfig.sheet_name` -- if specified, load only that sheet; if not, load the first sheet
- Handle merged cells (unmerge and fill values)
- Respect `FileSourceConfig.has_header` -- first row as headers or auto-generate `col_0`, `col_1`, etc.
- Detect and preserve date-formatted cells
- Skip fully empty rows
- Return `RawData` with `content_type=ContentType.TABULAR`

**Edge cases to handle:**
- Workbook with no sheets
- Sheet with no data
- Sheet with formula cells (read the computed value, not the formula)
- Sheet with mixed data types in a single column
- Very wide sheets (>100 columns)

**Example:**
```python
loader = XlsxLoader()
config = SourceConfig(
    source_type=SourceType.XLSX,
    name="quarterly_data",
    file=FileSourceConfig(path=Path("data/Q4.xlsx"), sheet_name="Revenue"),
)
raw = loader.load(config)
```

---

### Task 7.2: Implement the DOCX Loader

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/loaders/docx_loader.py`

**Description:** Load Word documents using `python-docx`. Extracts both text content and tables.

**Requirements:**
- Use `python-docx` to read `.docx` files
- Extract body paragraphs as text blocks (list of strings)
- Extract tables as tabular data (list of dicts per table)
- Return `RawData` with `content_type=ContentType.DOCUMENT`
- Store paragraphs in `document_text` field
- If tables are found, also populate `tabular_data` and `tabular_headers` (first table only, or all tables with metadata)
- Ignore headers/footers, tracked changes, and embedded images (V1 scope)

**Example:**
```python
loader = DocxLoader()
config = SourceConfig(
    source_type=SourceType.DOCX,
    name="report_draft",
    file=FileSourceConfig(path=Path("data/draft.docx")),
)
raw = loader.load(config)
# raw.document_text == ["Paragraph 1...", "Paragraph 2...", ...]
```

---

### Task 7.3: Implement the TXT Loader

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/loaders/txt_loader.py`

**Description:** Load plain text files. Simple line-by-line reading with encoding support.

**Requirements:**
- Read text file with configurable encoding (default: UTF-8)
- Split into paragraphs (double-newline separated) or lines
- Return `RawData` with `content_type=ContentType.DOCUMENT`
- Store content in `document_text` field

---

### Task 7.4: Implement the Markdown Loader

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/loaders/md_loader.py`

**Description:** Load Markdown files. Parses structure (headings, paragraphs, tables, code blocks) into structured document content.

**Requirements:**
- Read the raw markdown text
- Use `mistune` or a lightweight markdown parser to identify structure:
  - Headings (with level)
  - Paragraphs
  - Tables (if any, extract as tabular data)
  - Code blocks (preserve as-is)
  - Lists
- Return `RawData` with `content_type=ContentType.DOCUMENT`
- If markdown contains tables, also populate tabular fields
- Handle YAML frontmatter (if present, extract as metadata)

---

### Task 7.5: Implement the Document Normalizer

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/normalizers/document.py`

**Description:** Normalizes document-type raw data (from DOCX, TXT, MD) into a Dataset. Document data is stored differently than tabular data.

**Requirements:**
- For document content: create a Dataset with a single column `text` of type STRING, where each row is a paragraph/section
- Alternatively, create a structured representation with columns: `section_index`, `section_type` (heading, paragraph, table, etc.), `content`, `level`
- Include provenance tracking
- Handle documents that contain embedded tables (normalize those as tabular data in a separate Dataset if needed)

**Design decision (recommended approach):**
```python
# Document data becomes a DataFrame like:
# | section_index | section_type | level | content                    |
# |---------------|-------------|-------|----------------------------|
# | 0             | heading     | 1     | "Executive Summary"        |
# | 1             | paragraph   | 0     | "This report covers..."    |
# | 2             | heading     | 2     | "Key Findings"             |
# | 3             | paragraph   | 0     | "Revenue grew by 12%..."   |
```

---

### Task 7.6: Register All New Loaders

**File to update:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/loaders/__init__.py`

Update to include all new loaders and provide a factory function for creating a fully-registered registry:

```python
from .registry import LoaderRegistry
from .csv_loader import CsvLoader
from .json_loader import JsonLoader
from .xlsx_loader import XlsxLoader
from .docx_loader import DocxLoader
from .txt_loader import TxtLoader
from .md_loader import MdLoader


def create_default_registry() -> LoaderRegistry:
    """Create a LoaderRegistry with all built-in loaders registered."""
    registry = LoaderRegistry()
    registry.register(CsvLoader())
    registry.register(JsonLoader())
    registry.register(XlsxLoader())
    registry.register(DocxLoader())
    registry.register(TxtLoader())
    registry.register(MdLoader())
    return registry
```

---

### Task 7.7: Create Test Fixtures and Write Tests

**Test fixtures to create:**
- `/Volumes/SecondDrive/code2/pygramattic-reports/tests/fixtures/sample.xlsx` -- Simple workbook with one sheet, headers, and data
- `/Volumes/SecondDrive/code2/pygramattic-reports/tests/fixtures/sample.docx` -- Word doc with paragraphs and a table
- `/Volumes/SecondDrive/code2/pygramattic-reports/tests/fixtures/sample.txt` -- Plain text with paragraphs
- `/Volumes/SecondDrive/code2/pygramattic-reports/tests/fixtures/sample.md` -- Markdown with headings, paragraphs, and a table

**Note:** XLSX and DOCX fixtures should be generated programmatically in a test setup script or conftest fixture, since they are binary formats.

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_extended_loaders.py`

**Test cases:**
1. `test_xlsx_loader_basic` -- Load single-sheet XLSX
2. `test_xlsx_loader_specific_sheet` -- Load named sheet
3. `test_xlsx_loader_no_header` -- Auto-generate column names
4. `test_xlsx_loader_file_not_found` -- Raises `LoaderError`
5. `test_docx_loader_paragraphs` -- Extract text from DOCX
6. `test_docx_loader_with_table` -- Extract table from DOCX
7. `test_txt_loader_basic` -- Load plain text
8. `test_txt_loader_encoding` -- Handle non-UTF8 encoding
9. `test_md_loader_structure` -- Parse headings and paragraphs
10. `test_md_loader_with_table` -- Extract tables from markdown
11. `test_document_normalizer` -- Document raw data normalizes correctly
12. `test_default_registry_all_types` -- All types registered

---

## Dependencies

- **Depends on:** Phase 06 (loader base class, registry, tabular normalizer)
- **Blocks:** Phase 08 (CLI ingest command needs all loaders)

## Acceptance Criteria

1. `XlsxLoader` loads Excel files into `RawData`
2. `DocxLoader` loads Word documents into `RawData`
3. `TxtLoader` loads plain text into `RawData`
4. `MdLoader` loads Markdown into `RawData`
5. `DocumentNormalizer` converts document `RawData` into `Dataset`
6. `create_default_registry()` includes all loaders
7. All tests pass

## References

- PRD Input Handling: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 38-44)
- PRD Loaders Module: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 262-270)
