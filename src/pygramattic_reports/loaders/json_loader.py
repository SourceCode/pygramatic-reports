"""JSON file loader."""

from __future__ import annotations

import json
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

_logger = get_logger("loaders.json")


class JsonLoader(BaseLoader):
    """Loads JSON files into RawData objects.

    Detects whether the JSON is tabular (array of flat objects) or
    a document (nested structure) and sets the content type accordingly.
    """

    def load(self, config: SourceConfig) -> RawData:
        """Load a JSON file into a RawData object.

        Args:
            config: Source configuration with file path and options.

        Returns:
            RawData with appropriate content type.

        Raises:
            LoaderError: If the file cannot be read or parsed.
        """
        if config.file is None:
            msg = "JSON loader requires file configuration"
            raise LoaderError(msg, source_type="json")

        file_path = config.file.path
        if not file_path.is_file():
            msg = f"File not found: {file_path}"
            raise LoaderError(msg, source_type="json", source_path=str(file_path))

        checksum = self._compute_checksum(file_path)
        data = self._read_json(file_path, config.file.encoding)

        if _is_tabular(data):
            return self._build_tabular(data, config, checksum)
        return self._build_document(data, config, checksum)

    def supported_types(self) -> list[str]:
        """Return supported source types."""
        return [SourceType.JSON]

    @staticmethod
    def _compute_checksum(file_path: Path) -> str:
        """Compute SHA-256 checksum of the source file."""
        try:
            return compute_checksum(file_path)
        except OSError as exc:
            msg = f"Failed to compute checksum for {file_path}: {exc}"
            raise LoaderError(
                msg, source_type="json", source_path=str(file_path),
            ) from exc

    @staticmethod
    def _read_json(file_path: Path, encoding: str) -> Any:  # noqa: ANN401
        """Read and parse a JSON file."""
        try:
            text = file_path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            msg = f"Encoding error reading {file_path}: {exc}"
            raise LoaderError(
                msg, source_type="json", source_path=str(file_path),
            ) from exc
        except OSError as exc:
            msg = f"Failed to read {file_path}: {exc}"
            raise LoaderError(
                msg, source_type="json", source_path=str(file_path),
            ) from exc
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            msg = f"Invalid JSON in {file_path}: {exc}"
            raise LoaderError(
                msg, source_type="json", source_path=str(file_path),
            ) from exc

    @staticmethod
    def _build_tabular(
        data: list[dict[str, Any]],
        config: SourceConfig,
        checksum: str,
    ) -> RawData:
        """Build RawData for tabular JSON (array of flat objects)."""
        # Use union of all keys as headers to handle inconsistent keys
        headers: list[str] = []
        seen: set[str] = set()
        for row in data:
            for key in row:
                if key not in seen:
                    headers.append(key)
                    seen.add(key)

        # Convert all values to strings for consistency with CSV loader
        tabular_data = [
            {key: row.get(key) for key in headers}
            for row in data
        ]

        _logger.info(
            "Loaded tabular JSON",
            path=str(config.file.path) if config.file else "unknown",
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

    @staticmethod
    def _build_document(
        data: Any,  # noqa: ANN401
        config: SourceConfig,
        checksum: str,
    ) -> RawData:
        """Build RawData for document JSON (nested structure)."""
        document_text = [json.dumps(data, indent=2, default=str)]

        _logger.info(
            "Loaded document JSON",
            path=str(config.file.path) if config.file else "unknown",
        )

        return RawData(
            id=generate_id(),
            source_config=config,
            content_type=ContentType.DOCUMENT,
            document_text=document_text,
            loaded_at=now_utc(),
            source_checksum=checksum,
        )


def _is_flat_dict(obj: Any) -> bool:  # noqa: ANN401
    """Check if an object is a dict with only scalar values."""
    if not isinstance(obj, dict):
        return False
    return all(not isinstance(v, (dict, list)) for v in obj.values())


def _is_tabular(data: Any) -> bool:  # noqa: ANN401
    """Detect if JSON data is tabular (array of flat objects)."""
    if not isinstance(data, list) or len(data) == 0:
        return False
    return all(_is_flat_dict(item) for item in data)
