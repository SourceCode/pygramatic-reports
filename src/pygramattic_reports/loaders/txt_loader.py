"""Plain text file loader."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pygramattic_reports.exceptions import LoaderError
from pygramattic_reports.logging import get_logger
from pygramattic_reports.models import ContentType, RawData, SourceType
from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.storage.checksum import compute_checksum

from .base import BaseLoader

if TYPE_CHECKING:
    from pathlib import Path

    from pygramattic_reports.models import SourceConfig

_logger = get_logger("loaders.txt")

_PARAGRAPH_SPLIT = re.compile(r"\n{2,}")


class TxtLoader(BaseLoader):
    """Loads plain text files into RawData objects.

    Splits text into paragraphs (double-newline separated) and
    stores them as ``document_text`` entries.
    """

    def load(self, config: SourceConfig) -> RawData:
        """Load a text file into a RawData object.

        Args:
            config: Source configuration with file path and options.

        Returns:
            RawData with ``content_type=DOCUMENT``.

        Raises:
            LoaderError: If the file cannot be read.
        """
        if config.file is None:
            msg = "TXT loader requires file configuration"
            raise LoaderError(msg, source_type="txt")

        file_path = config.file.path
        if not file_path.is_file():
            msg = f"File not found: {file_path}"
            raise LoaderError(msg, source_type="txt", source_path=str(file_path))

        checksum = _compute_checksum(file_path)
        text = _read_file(file_path, config.file.encoding)
        paragraphs = _split_paragraphs(text)

        _logger.info(
            "Loaded TXT file",
            path=str(file_path),
            paragraphs=len(paragraphs),
        )

        return RawData(
            id=generate_id(),
            source_config=config,
            content_type=ContentType.DOCUMENT,
            document_text=paragraphs,
            loaded_at=now_utc(),
            source_checksum=checksum,
        )

    def supported_types(self) -> list[str]:
        """Return supported source types."""
        return [SourceType.TXT]


def _compute_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of the source file."""
    try:
        return compute_checksum(file_path)
    except OSError as exc:
        msg = f"Failed to compute checksum for {file_path}: {exc}"
        raise LoaderError(msg, source_type="txt", source_path=str(file_path)) from exc


def _read_file(file_path: Path, encoding: str) -> str:
    """Read the entire file as text."""
    try:
        return file_path.read_text(encoding=encoding)
    except UnicodeDecodeError as exc:
        msg = f"Encoding error reading {file_path}: {exc}"
        raise LoaderError(msg, source_type="txt", source_path=str(file_path)) from exc
    except OSError as exc:
        msg = f"Failed to read {file_path}: {exc}"
        raise LoaderError(msg, source_type="txt", source_path=str(file_path)) from exc


def _split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs on double newlines, stripping whitespace."""
    return [p.strip() for p in _PARAGRAPH_SPLIT.split(text.strip()) if p.strip()]
