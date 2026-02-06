# Phase 05: Storage Manager

## Objective

Implement the storage subsystem that manages the `data/` directory structure, persists datasets, tracks metadata via manifest files, and provides a clean interface for all modules to save and retrieve data.

## Why This Phase Is Fifth

Nearly every module reads from or writes to storage. Loaders save raw data, normalizers save processed datasets, the builder saves reports, and the chart engine saves media. The Storage Manager must exist before any of these modules can persist their output.

## Tasks

### Task 5.1: Implement the Storage Manager

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/storage/manager.py`

**Description:** The core storage manager handles directory creation, dataset persistence, manifest tracking, and file retrieval.

**Interface:**

```python
from pathlib import Path
from pygramattic_reports.models import Dataset, Manifest
from pygramattic_reports.config import AppConfig


class StorageManager:
    """Manages the data/ directory structure and dataset persistence.

    Directory layout:
        data/
          raw/{dataset_id}/
            manifest.json
            data.csv (or .json, .parquet)
          processed/{dataset_id}/
            manifest.json
            data.parquet
          derived/{dataset_id}/
            manifest.json
            data.parquet
          reports/{report_id}/
            manifest.json
            report.docx (or .md, etc.)
            build_log.json
          media/{report_id}/
            chart_001.png
            chart_002.png

    Usage:
        storage = StorageManager(config)
        storage.initialize()  # Create directory structure

        # Save a raw dataset
        dataset_id = storage.save_raw(raw_data, source_config)

        # Save a processed dataset
        storage.save_processed(dataset)

        # Retrieve a dataset
        dataset = storage.load_dataset(dataset_id, stage="processed")

        # Save a report
        storage.save_report(report_id, content_bytes, format="docx")

        # Save a chart image
        media_path = storage.save_media(report_id, chart_bytes, "chart_001.png")
    """

    def __init__(self, config: AppConfig):
        """Initialize storage manager with application config."""
        ...

    def initialize(self) -> None:
        """Create the data/ directory structure if it does not exist.

        Creates: raw/, processed/, derived/, reports/, media/
        Idempotent: safe to call multiple times.
        """
        ...

    def save_raw(self, data: bytes | str, metadata: dict, format: str = "csv") -> str:
        """Save raw ingested data to data/raw/{id}/.

        Args:
            data: Raw file content
            metadata: Source metadata (type, path, row count, etc.)
            format: File format extension

        Returns:
            Dataset ID (UUID string)

        Creates:
            data/raw/{id}/manifest.json
            data/raw/{id}/data.{format}
        """
        ...

    def save_dataset(self, dataset: Dataset, stage: str = "processed") -> str:
        """Save a normalized Dataset to the specified stage directory.

        Args:
            dataset: The Dataset object (with DataFrame)
            stage: "processed" or "derived"

        Returns:
            Dataset ID

        Creates:
            data/{stage}/{id}/manifest.json
            data/{stage}/{id}/data.parquet (or .csv as fallback)
        """
        ...

    def load_dataset(self, dataset_id: str, stage: str = "processed") -> Dataset:
        """Load a Dataset from storage by ID.

        Args:
            dataset_id: UUID of the dataset
            stage: Which directory to look in

        Returns:
            Reconstructed Dataset with DataFrame loaded

        Raises:
            StorageError: If dataset not found or manifest corrupt
        """
        ...

    def get_manifest(self, dataset_id: str, stage: str = "processed") -> Manifest:
        """Load just the manifest for a dataset without loading the data.

        Useful for listing and querying datasets without memory overhead.
        """
        ...

    def list_datasets(self, stage: str | None = None) -> list[Manifest]:
        """List all datasets, optionally filtered by stage.

        Returns manifests sorted by creation date (newest first).
        """
        ...

    def save_report(
        self, report_id: str, content: bytes, filename: str, build_log: dict | None = None
    ) -> Path:
        """Save a generated report file.

        Args:
            report_id: UUID of the report
            content: Report file content
            filename: Output filename (e.g., "report.docx")
            build_log: Optional build log dict to save alongside

        Returns:
            Path to the saved report file
        """
        ...

    def save_media(self, report_id: str, content: bytes, filename: str) -> Path:
        """Save a media file (chart image) associated with a report.

        Args:
            report_id: UUID of the report this media belongs to
            content: Image bytes
            filename: Filename (e.g., "chart_revenue.png")

        Returns:
            Path to the saved media file
        """
        ...

    def resolve_path(self, stage: str, dataset_id: str) -> Path:
        """Resolve the full filesystem path for a dataset directory."""
        ...
```

**Implementation requirements:**
- Use `pathlib.Path` for all path operations
- Use atomic writes: write to a temp file, then rename (prevents corruption on crash)
- Generate UUIDs for dataset IDs
- Compute SHA-256 checksums for all saved data files
- Manifest files are JSON with the `Manifest` model schema
- Save DataFrames as Parquet (primary) with CSV fallback
- All operations should log via `get_logger("storage")`
- Raise `StorageError` for all failures

---

### Task 5.2: Implement Manifest Serialization

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/storage/manifest_io.py`

**Description:** Handle reading and writing manifest.json files.

```python
from pathlib import Path
from pygramattic_reports.models import Manifest


def write_manifest(manifest: Manifest, directory: Path) -> Path:
    """Write a manifest.json file to the specified directory.

    Uses atomic write (write to temp, then rename).

    Returns:
        Path to the written manifest file.
    """
    ...


def read_manifest(directory: Path) -> Manifest:
    """Read and parse a manifest.json file from a directory.

    Raises:
        StorageError: If file missing, corrupt, or schema-invalid.
    """
    ...
```

---

### Task 5.3: Implement Checksum Utility

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/storage/checksum.py`

```python
from pathlib import Path


def compute_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file.

    Reads file in chunks to handle large files without loading
    everything into memory.

    Returns:
        Hex-encoded SHA-256 hash string.
    """
    ...


def verify_checksum(file_path: Path, expected: str) -> bool:
    """Verify a file's checksum matches the expected value."""
    ...
```

---

### Task 5.4: Create Storage Package Init

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/storage/__init__.py`

```python
"""Storage manager for pygramattic-reports.

Handles the data/ directory structure, dataset persistence, and metadata tracking.

Usage:
    from pygramattic_reports.storage import StorageManager

    storage = StorageManager(config)
    storage.initialize()
    dataset_id = storage.save_dataset(dataset)
"""
from .manager import StorageManager

__all__ = ["StorageManager"]
```

---

### Task 5.5: Write Comprehensive Storage Tests

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_storage.py`

**Test cases:**

1. **`test_initialize_creates_directories`** -- Verify all subdirectories are created
2. **`test_initialize_is_idempotent`** -- Running initialize twice does not error
3. **`test_save_raw_creates_manifest_and_data`** -- Raw data is saved with manifest
4. **`test_save_dataset_creates_parquet`** -- Dataset DataFrame saved as parquet
5. **`test_load_dataset_roundtrip`** -- Save then load produces equivalent Dataset
6. **`test_load_dataset_not_found`** -- StorageError for missing dataset
7. **`test_manifest_roundtrip`** -- Write then read manifest produces same object
8. **`test_list_datasets`** -- Lists all datasets in a stage
9. **`test_save_report`** -- Report file saved correctly
10. **`test_save_media`** -- Media file saved in correct location
11. **`test_checksum_computation`** -- Checksums are computed and verifiable
12. **`test_atomic_write`** -- Interrupted write does not leave corrupt files (if testable)

**Example:**
```python
import pandas as pd
import pytest
from pygramattic_reports.storage import StorageManager
from pygramattic_reports.models import Dataset, ColumnSchema, DataType, Provenance, now_utc, generate_id
from pygramattic_reports.config import load_config


@pytest.fixture
def storage(tmp_path):
    config = load_config(overrides={"storage": {"data_dir": str(tmp_path)}})
    mgr = StorageManager(config)
    mgr.initialize()
    return mgr


def test_initialize_creates_directories(storage, tmp_path):
    for subdir in ["raw", "processed", "derived", "reports", "media"]:
        assert (tmp_path / subdir).is_dir()


def test_save_and_load_dataset(storage):
    df = pd.DataFrame({"region": ["US", "EU"], "revenue": [1000, 2000]})
    dataset = Dataset(
        id=generate_id(),
        name="revenue",
        schema=[
            ColumnSchema(name="region", dtype=DataType.STRING),
            ColumnSchema(name="revenue", dtype=DataType.INTEGER),
        ],
        dataframe=df,
        provenance=Provenance(
            source_type="csv", source_name="test",
            loaded_at=now_utc(), normalized_at=now_utc(), row_count_raw=2,
        ),
    )
    storage.save_dataset(dataset)
    loaded = storage.load_dataset(dataset.id)
    assert loaded.row_count == 2
    assert list(loaded.dataframe.columns) == ["region", "revenue"]
```

---

## Dependencies

- **Depends on:** Phase 01 (scaffold), Phase 02 (models: Dataset, Manifest), Phase 03 (config), Phase 04 (exceptions, logging)
- **Blocks:** Phase 06 (loaders save to storage), Phase 13 (builder saves reports), Phase 12 (chart engine saves media)

## Acceptance Criteria

1. `StorageManager.initialize()` creates the full directory structure
2. Datasets can be saved and loaded (roundtrip) with data integrity
3. Manifest files are valid JSON matching the `Manifest` model
4. Checksums are computed and stored in manifests
5. `list_datasets()` returns correct results
6. All storage operations raise `StorageError` on failure
7. All tests pass

## References

- PRD Storage System: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 72-88)
- PRD Data Directory Structure: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 75-82)
- PRD Storage Manager Module: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 294-301)
