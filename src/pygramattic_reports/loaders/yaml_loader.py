"""YAML loader for pygramattic-reports."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import yaml

from pygramattic_reports.exceptions import LoaderError
from pygramattic_reports.loaders.base import BaseLoader
from pygramattic_reports.models.raw_data import ContentType, RawData

if TYPE_CHECKING:
    from pygramattic_reports.models import SourceConfig


class YamlLoader(BaseLoader):
    """Parses YAML files into RawData."""

    def load(self, config: SourceConfig) -> RawData:
        """Load YAML file into RawData.

        Args:
            config: Source configuration.

        Returns:
            RawData containing the parsed content.

        Raises:
            LoaderError: If the file cannot be read or parsed.
        """
        if not config.file:
            msg = "SourceConfig.file is required for YamlLoader"
            raise LoaderError(msg, path=str(config.source_type))

        path = config.file.path
        if not path.exists():
            msg = f"YAML file not found: {path}"
            raise LoaderError(msg, path=str(path))

        try:
            with path.open("r", encoding="utf-8") as f:
                content = yaml.safe_load(f)

            # Determine content type based on structure
            content_type = ContentType.DOCUMENT  # Default
            tabular_data = None
            tabular_headers = None
            row_count = None

            # Rudimentary detection: list of dicts -> tabular
            if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict):
                content_type = ContentType.TABULAR
                tabular_data = content
                tabular_headers = list(content[0].keys())
                row_count = len(content)

            return RawData(
                id=str(uuid.uuid4()),
                source_config=config,
                content_type=content_type,
                tabular_data=tabular_data,
                tabular_headers=tabular_headers,
                row_count=row_count,
                loaded_at=datetime.now(),
                # If not tabular, strictly speaking we might need a 'document_object' field
                # but RawData currently only has tabular_data and document_text.
                # For now, we will assume YAML is mostly used for tabular-like data
                # or we leverage document_text as a JSON dump if strict structure is needed.
                # Or we update RawData model to support 'structured_content' (not in scope right now)
                document_text=[str(content)] if content_type != ContentType.TABULAR else None,
                source_checksum=None,
            )
        except Exception as e:
            msg = f"Failed to load YAML file: {path}. Error: {e}"
            raise LoaderError(msg, path=str(path)) from e

    def supported_types(self) -> list[str]:
        """Return supported source types."""
        return ["yaml", "yml"]
