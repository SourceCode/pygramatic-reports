"""Abstract base class for data loaders."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygramattic_reports.models import RawData, SourceConfig


class BaseLoader(ABC):
    """Abstract base class for data loaders.

    Each loader reads a specific input format and produces a RawData object.
    Loaders do NOT interpret or transform data -- they only read it.

    Subclasses must implement:
        - ``load(config) -> RawData``
        - ``supported_types() -> list[str]``
    """

    @abstractmethod
    def load(self, config: SourceConfig) -> RawData:
        """Load data from the configured source.

        Args:
            config: Source configuration with path, options, etc.

        Returns:
            RawData with the raw content loaded from the source.

        Raises:
            LoaderError: If the source cannot be read.
        """
        ...

    @abstractmethod
    def supported_types(self) -> list[str]:
        """Return the list of SourceType values this loader handles."""
        ...
