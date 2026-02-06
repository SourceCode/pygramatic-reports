"""Dataset model for pygramattic-reports.

Defines the Dataset type -- the central data structure that flows through
processors, builders, charts, validators, and converters.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict

from .base import now_utc

if TYPE_CHECKING:
    import pandas as pd


class DataType(StrEnum):
    """Supported column data types."""

    STRING = "string"
    INTEGER = "int"
    FLOAT = "float"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"


class ColumnSchema(BaseModel):
    """Schema for a single column in a Dataset.

    Attributes:
        name: Column name.
        dtype: Column data type.
        nullable: Whether the column allows null values.
        description: Optional column description.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    dtype: DataType
    nullable: bool = True
    description: str | None = None


class Provenance(BaseModel):
    """Tracks where a dataset came from.

    Attributes:
        source_type: Source type identifier.
        source_path: File path or connection string.
        source_name: Human-readable source name.
        loaded_at: When the data was loaded.
        normalized_at: When the data was normalized.
        row_count_raw: Row count before normalization.
        transformations: List of transformations applied.
    """

    model_config = ConfigDict(frozen=True)

    source_type: str
    source_path: str | None = None
    source_name: str
    loaded_at: datetime
    normalized_at: datetime
    row_count_raw: int
    transformations: list[str] = []


class Dataset:
    """The central data structure in pygramattic-reports.

    Wraps a pandas DataFrame with typed schema, provenance tracking,
    and metadata. This is NOT a Pydantic model because it holds a
    DataFrame, which is not natively serializable.

    Output of Normalizer. Input to Processors, Converters, Charts, Builder.

    Attributes:
        id: Unique dataset identifier.
        name: Human-readable dataset name.
        schema: Column schema definitions.
        dataframe: The underlying pandas DataFrame.
        provenance: Data provenance tracking.
        created_at: When the dataset was created.
    """

    def __init__(  # noqa: D107
        self,
        *,
        id: str,  # noqa: A002
        name: str,
        schema: list[ColumnSchema],
        dataframe: pd.DataFrame,
        provenance: Provenance,
        created_at: datetime | None = None,
    ) -> None:
        self.id = id
        self.name = name
        self.schema = schema
        self.dataframe = dataframe
        self.provenance = provenance
        self.created_at = created_at if created_at is not None else now_utc()

    @property
    def row_count(self) -> int:
        """Number of rows in the dataset."""
        return len(self.dataframe)

    @property
    def column_names(self) -> list[str]:
        """List of column names from the schema."""
        return [col.name for col in self.schema]

    def to_metadata_dict(self) -> dict[str, Any]:
        """Serialize metadata without the DataFrame for manifest storage.

        Returns:
            Dictionary of dataset metadata.
        """
        return {
            "id": self.id,
            "name": self.name,
            "schema": [col.model_dump() for col in self.schema],
            "row_count": self.row_count,
            "provenance": self.provenance.model_dump(),
            "created_at": self.created_at.isoformat(),
        }
