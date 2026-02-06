"""Raw data model for pygramattic-reports.

Defines the RawData type -- the output of Loaders, input to Normalizers.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from .base import PygramatticModel
from .sources import SourceConfig


class ContentType(StrEnum):
    """Type of content contained in raw data."""

    TABULAR = "tabular"
    DOCUMENT = "document"
    PRESENTATION = "presentation"


class RawData(PygramatticModel):
    """Output of a Loader containing unprocessed data.

    This is the bridge between input-specific loading and format-agnostic
    normalization. Loaders produce RawData; Normalizers consume it.

    Attributes:
        id: Unique identifier.
        source_config: Where this data came from.
        content_type: What kind of data this is.
        tabular_data: List of row dicts for tabular content.
        tabular_headers: Column headers for tabular content.
        document_text: List of text blocks for document content.
        row_count: Number of rows in tabular data.
        loaded_at: When the data was loaded.
        source_checksum: SHA-256 of the source file.
    """

    id: str
    source_config: SourceConfig
    content_type: ContentType
    tabular_data: list[dict[str, Any]] | None = None
    tabular_headers: list[str] | None = None
    document_text: list[str] | None = None
    row_count: int | None = None
    loaded_at: datetime
    source_checksum: str | None = None
