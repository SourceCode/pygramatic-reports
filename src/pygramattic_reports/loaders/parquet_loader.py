"""Parquet loader for pygramattic-reports."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

import pandas as pd

from pygramattic_reports.exceptions import LoaderError
from pygramattic_reports.loaders.base import BaseLoader
from pygramattic_reports.models.raw_data import ContentType, RawData

if TYPE_CHECKING:
    from pygramattic_reports.models import SourceConfig


class ParquetLoader(BaseLoader):
    """Parses Parquet files into RawData using pandas."""

    def load(self, config: SourceConfig) -> RawData:
        """Load Parquet file into RawData.

        Args:
            config: Source configuration.

        Returns:
            RawData containing the parsed records.

        Raises:
            LoaderError: If the file cannot be read or parsed.
        """
        if not config.file:
            msg = "SourceConfig.file is required for ParquetLoader"
            raise LoaderError(msg, path=str(config.source_type))

        path = config.file.path
        if not path.exists():
            msg = f"Parquet file not found: {path}"
            raise LoaderError(msg, path=str(path))

        try:
            # Using pandas to read parquet is efficient and handles pyarrow deps
            df = pd.read_parquet(path)

            # Convert NaN to None for JSON compliance
            # cast to object to allow mixed types (None + float)
            df = df.astype(object).where(pd.notnull(df), None)  # type: ignore[arg-type]

            # Helper to ensure keys are strings
            records: list[dict[str, Any]] = [
                {str(k): v for k, v in record.items()} for record in df.to_dict(orient="records")
            ]

            return RawData(
                id=str(uuid.uuid4()),
                source_config=config,
                content_type=ContentType.TABULAR,
                tabular_data=records,
                tabular_headers=[str(c) for c in df.columns],
                row_count=len(df),
                loaded_at=datetime.now(),
                source_checksum=None,  # Checksum support could be added later
            )
        except Exception as e:
            msg = f"Failed to load Parquet file: {path}. Error: {e}"
            raise LoaderError(msg, path=str(path)) from e

    def supported_types(self) -> list[str]:
        """Return supported source types."""
        return ["parquet"]
