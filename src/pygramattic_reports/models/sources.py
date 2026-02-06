"""Source configuration models for pygramattic-reports.

Defines typed configuration for each input source type supported
by the data loading pipeline.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class SourceType(StrEnum):
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
    """Configuration for file-based sources.

    Attributes:
        path: Path to the source file.
        encoding: File encoding.
        sheet_name: XLSX sheet to read.
        delimiter: CSV field delimiter.
        has_header: Whether the first row is a header.
    """

    model_config = ConfigDict(frozen=True)

    path: Path
    encoding: str = "utf-8"
    sheet_name: str | None = None
    delimiter: str = ","
    has_header: bool = True


class DatabaseSourceConfig(BaseModel):
    """Configuration for PostgreSQL source.

    Attributes:
        host: Database host.
        port: Database port.
        database: Database name.
        schema_name: Database schema.
        query: Custom SQL query.
        table: Table name.
        username: Database username.
        password: Database password.
    """

    model_config = ConfigDict(frozen=True)

    host: str
    port: int = 5432
    database: str
    schema_name: str = "public"
    query: str | None = None
    table: str | None = None
    username: str | None = None
    password: str | None = None


class GoogleSourceConfig(BaseModel):
    """Configuration for Google Workspace sources.

    Attributes:
        document_id: Google document/spreadsheet/presentation ID.
        credentials_path: Path to service account credentials.
        sheet_name: Specific sheet name for Google Sheets.
    """

    model_config = ConfigDict(frozen=True)

    document_id: str
    credentials_path: Path | None = None
    sheet_name: str | None = None


class SourceConfig(BaseModel):
    """Unified source configuration.

    Combines source type with the appropriate typed configuration
    for that source.

    Attributes:
        source_type: The type of input source.
        name: Human-readable name for this source.
        file: File source configuration.
        database: Database source configuration.
        google: Google Workspace source configuration.
    """

    model_config = ConfigDict(frozen=True)

    source_type: SourceType
    name: str
    file: FileSourceConfig | None = None
    database: DatabaseSourceConfig | None = None
    google: GoogleSourceConfig | None = None
