"""Manifest model for pygramattic-reports.

Defines the Manifest model for dataset metadata stored by the Storage Manager.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .dataset import ColumnSchema


class Manifest(BaseModel):
    """Metadata file stored alongside each dataset in the storage system.

    Persisted as ``manifest.json`` in each dataset's directory.

    Attributes:
        id: Dataset ID.
        name: Human-readable name.
        source_type: Original source type.
        source_path: Original file path or connection info.
        columns: Column definitions.
        row_count: Number of rows.
        checksum: SHA-256 of the data file.
        created_at: When the dataset was created.
        storage_path: Relative path within data directory.
        format: Storage format.
        size_bytes: File size on disk.
        tags: User-defined tags.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    source_type: str
    source_path: str | None = None
    columns: list[ColumnSchema]
    row_count: int
    checksum: str | None = None
    created_at: datetime
    storage_path: str
    format: str = "parquet"
    size_bytes: int | None = None
    tags: list[str] = []
