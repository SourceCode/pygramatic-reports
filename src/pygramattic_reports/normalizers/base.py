"""Abstract base class for data normalizers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygramattic_reports.models import RawData
    from pygramattic_reports.models.dataset import Dataset


class BaseNormalizer(ABC):
    """Abstract base class for data normalizers.

    Normalizers convert RawData (raw loaded content) into typed Dataset
    objects. This is where schema inference, type coercion, and data
    cleanup happen.
    """

    @abstractmethod
    def normalize(self, raw_data: RawData) -> Dataset:
        """Normalize raw data into a typed Dataset.

        This involves:
            1. Inferring column types (string, int, float, date, boolean)
            2. Coercing values to inferred types
            3. Building the schema (list of ColumnSchema)
            4. Creating the pandas DataFrame
            5. Recording provenance

        Args:
            raw_data: Raw loaded data from a Loader.

        Returns:
            A typed, validated Dataset.

        Raises:
            NormalizationError: If data cannot be normalized.
        """
        ...
