"""Loader registry for mapping source types to implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygramattic_reports.exceptions import LoaderError

if TYPE_CHECKING:
    from pygramattic_reports.models import SourceType

    from .base import BaseLoader


class LoaderRegistry:
    """Registry of loader implementations.

    Usage::

        registry = LoaderRegistry()
        registry.register(CsvLoader())
        registry.register(JsonLoader())

        loader = registry.get_loader(SourceType.CSV)
        raw_data = loader.load(source_config)
    """

    def __init__(self) -> None:  # noqa: D107
        self._loaders: dict[str, BaseLoader] = {}

    def register(self, loader: BaseLoader) -> None:
        """Register a loader for its supported types.

        Args:
            loader: Loader instance to register.
        """
        for source_type in loader.supported_types():
            self._loaders[source_type] = loader

    def get_loader(self, source_type: SourceType) -> BaseLoader:
        """Get the loader for a given source type.

        Args:
            source_type: The source type to look up.

        Returns:
            The registered loader.

        Raises:
            LoaderError: If no loader is registered for this type.
        """
        loader = self._loaders.get(source_type.value)
        if loader is None:
            msg = f"No loader registered for source type: {source_type.value}"
            raise LoaderError(msg, source_type=source_type.value)
        return loader

    def available_types(self) -> list[str]:
        """List all registered source types."""
        return list(self._loaders.keys())


def create_default_loader_registry() -> LoaderRegistry:
    """Create a registry pre-loaded with built-in loaders.

    Returns:
        Registry with csv, json, xlsx, docx, md, txt, parquet, yaml loaders.
    """
    from .csv_loader import CsvLoader  # noqa: PLC0415
    from .docx_loader import DocxLoader  # noqa: PLC0415
    from .json_loader import JsonLoader  # noqa: PLC0415
    from .md_loader import MdLoader  # noqa: PLC0415
    from .parquet_loader import ParquetLoader  # noqa: PLC0415
    from .txt_loader import TxtLoader  # noqa: PLC0415
    from .xlsx_loader import XlsxLoader  # noqa: PLC0415
    from .yaml_loader import YamlLoader  # noqa: PLC0415

    registry = LoaderRegistry()
    registry.register(CsvLoader())
    registry.register(JsonLoader())
    registry.register(XlsxLoader())
    registry.register(DocxLoader())
    registry.register(MdLoader())
    registry.register(TxtLoader())
    registry.register(ParquetLoader())
    registry.register(YamlLoader())

    return registry
