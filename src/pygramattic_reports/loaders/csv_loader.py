"""CSV file loader."""

from __future__ import annotations

import csv
from typing import TYPE_CHECKING, Any

from pygramattic_reports.exceptions import LoaderError
from pygramattic_reports.logging import get_logger
from pygramattic_reports.models import ContentType, RawData, SourceType
from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.storage.checksum import compute_checksum

from .base import BaseLoader

if TYPE_CHECKING:
    from pathlib import Path

    from pygramattic_reports.models import SourceConfig

_logger = get_logger("loaders.csv")


class CsvLoader(BaseLoader):
    """Loads CSV files into RawData objects.

    Respects ``FileSourceConfig`` settings for delimiter, encoding,
    and header presence.
    """

    def load(self, config: SourceConfig) -> RawData:
        """Load a CSV file into a RawData object.

        Args:
            config: Source configuration with file path and options.

        Returns:
            RawData with ``content_type=TABULAR``.

        Raises:
            LoaderError: If the file cannot be read or parsed.
        """
        if config.file is None:
            msg = "CSV loader requires file configuration"
            raise LoaderError(msg, source_type="csv")

        file_path = config.file.path
        if not file_path.is_file():
            msg = f"File not found: {file_path}"
            raise LoaderError(msg, source_type="csv", source_path=str(file_path))

        encoding = config.file.encoding
        # Use utf-8-sig to transparently strip BOM when present
        if encoding.lower().replace("-", "") == "utf8":
            encoding = "utf-8-sig"

        checksum = self._compute_checksum(file_path)
        headers, tabular_data = self._read_csv(
            file_path,
            encoding=encoding,
            delimiter=config.file.delimiter,
            has_header=config.file.has_header,
        )

        _logger.info(
            "Loaded CSV file",
            path=str(file_path),
            rows=len(tabular_data),
            columns=len(headers),
        )

        return RawData(
            id=generate_id(),
            source_config=config,
            content_type=ContentType.TABULAR,
            tabular_data=tabular_data,
            tabular_headers=headers,
            row_count=len(tabular_data),
            loaded_at=now_utc(),
            source_checksum=checksum,
        )

    def supported_types(self) -> list[str]:
        """Return supported source types."""
        return [SourceType.CSV]

    @staticmethod
    def _compute_checksum(file_path: Path) -> str:
        """Compute SHA-256 checksum of the source file."""
        try:
            return compute_checksum(file_path)
        except OSError as exc:
            msg = f"Failed to compute checksum for {file_path}: {exc}"
            raise LoaderError(msg, source_type="csv", source_path=str(file_path)) from exc

    @staticmethod
    def _read_csv(
        file_path: Path,
        *,
        encoding: str,
        delimiter: str,
        has_header: bool,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """Read CSV file and return headers and row dicts."""
        try:
            with file_path.open(encoding=encoding, newline="") as f:
                reader = csv.reader(f, delimiter=delimiter)

                if has_header:
                    headers = next(reader, [])
                else:
                    first_row = next(reader, None)
                    if first_row is None:
                        return [], []
                    headers = [f"col_{i}" for i in range(len(first_row))]
                    # Put the first row back into the data
                    rows = [first_row, *list(reader)]
                    return headers, [
                        dict(zip(headers, _pad_row(row, len(headers)), strict=False))
                        for row in rows
                    ]

                rows = list(reader)
        except UnicodeDecodeError as exc:
            msg = f"Encoding error reading {file_path}: {exc}"
            raise LoaderError(msg, source_type="csv", source_path=str(file_path)) from exc
        except csv.Error as exc:
            msg = f"CSV parsing error in {file_path}: {exc}"
            raise LoaderError(msg, source_type="csv", source_path=str(file_path)) from exc
        except OSError as exc:
            msg = f"Failed to read {file_path}: {exc}"
            raise LoaderError(msg, source_type="csv", source_path=str(file_path)) from exc

        tabular_data = [
            dict(zip(headers, _pad_row(row, len(headers)), strict=False))
            for row in rows
        ]
        return headers, tabular_data


def _pad_row(row: list[str], expected_len: int) -> list[str]:
    """Pad a CSV row with empty strings if it has fewer fields than expected."""
    if len(row) >= expected_len:
        return row
    return row + [""] * (expected_len - len(row))
