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
