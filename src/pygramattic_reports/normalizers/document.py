"""Document data normalizer."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pandas as pd

from pygramattic_reports.exceptions import NormalizationError
from pygramattic_reports.logging import get_logger
from pygramattic_reports.models import ColumnSchema, ContentType, DataType, Provenance
from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.models.dataset import Dataset

from .base import BaseNormalizer

if TYPE_CHECKING:
    from pygramattic_reports.models import RawData

_logger = get_logger("normalizers.document")

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_CODE_BLOCK_RE = re.compile(r"^```")

_SECTION_SCHEMA = [
    ColumnSchema(name="section_index", dtype=DataType.INTEGER, nullable=False),
    ColumnSchema(name="section_type", dtype=DataType.STRING, nullable=False),
    ColumnSchema(name="level", dtype=DataType.INTEGER, nullable=False),
    ColumnSchema(name="content", dtype=DataType.STRING, nullable=False),
]


class DocumentNormalizer(BaseNormalizer):
    """Normalizes document-type raw data into a structured Dataset.

    Creates a DataFrame with columns: ``section_index``, ``section_type``,
    ``level``, and ``content``. Each row represents a document section
    (heading, paragraph, code block, or list).
    """

    def normalize(self, raw_data: RawData) -> Dataset:
        """Normalize document RawData into a Dataset.

        Args:
            raw_data: Raw data with ``content_type=DOCUMENT``.

        Returns:
            Dataset with structured section data.

        Raises:
            NormalizationError: If the data is not document type.
        """
        if raw_data.content_type != ContentType.DOCUMENT:
            msg = f"Expected document data, got {raw_data.content_type}"
            raise NormalizationError(msg)

        blocks = raw_data.document_text or []
        sections = _classify_blocks(blocks)

        df = pd.DataFrame(sections, columns=["section_index", "section_type", "level", "content"])

        _logger.info(
            "Normalized document data",
            sections=len(sections),
            types={s[1] for s in sections},
        )

        return Dataset(
            id=generate_id(),
            name=raw_data.source_config.name,
            schema=list(_SECTION_SCHEMA),
            dataframe=df,
            provenance=_build_provenance(raw_data),
        )


def _build_provenance(raw_data: RawData) -> Provenance:
    """Build provenance from RawData source info."""
    return Provenance(
        source_type=raw_data.source_config.source_type.value,
        source_name=raw_data.source_config.name,
        source_path=(
            str(raw_data.source_config.file.path)
            if raw_data.source_config.file
            else None
        ),
        loaded_at=raw_data.loaded_at,
        normalized_at=now_utc(),
        row_count_raw=len(raw_data.document_text) if raw_data.document_text else 0,
    )


def _classify_blocks(blocks: list[str]) -> list[tuple[int, str, int, str]]:
    """Classify each text block into section type and level.

    Returns:
        List of (section_index, section_type, level, content) tuples.
    """
    sections: list[tuple[int, str, int, str]] = []
    for i, block in enumerate(blocks):
        section_type, level, content = _classify_block(block)
        sections.append((i, section_type, level, content))
    return sections


def _classify_block(block: str) -> tuple[str, int, str]:
    """Classify a single text block.

    Returns:
        Tuple of (section_type, level, content).
    """
    heading_match = _HEADING_RE.match(block)
    if heading_match:
        level = len(heading_match.group(1))
        return "heading", level, heading_match.group(2).strip()

    if _CODE_BLOCK_RE.match(block):
        lines = block.split("\n")
        # Strip the opening and closing ``` lines
        content = "\n".join(lines[1:-1]) if len(lines) > 2 else ""  # noqa: PLR2004
        return "code", 0, content

    if block.startswith(("- ", "* ", "1. ", "1) ")):
        return "list", 0, block

    return "paragraph", 0, block
