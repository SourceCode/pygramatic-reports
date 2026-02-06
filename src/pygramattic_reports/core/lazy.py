"""Lazy loading support for Datasets.

Allows datasets to be defined without immediately loading their data into memory.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from pygramattic_reports.models import Dataset, now_utc

if TYPE_CHECKING:
    import pandas as pd

    from pygramattic_reports.models import ColumnSchema, Provenance

# Tuple of (DataFrame, Schema, Provenance)
LoaderResult = tuple["pd.DataFrame", list["ColumnSchema"], "Provenance"]


class LazyDataset(Dataset):
    """A Dataset that loads its data on first access.

    This class mimics the interface of ``Dataset`` but defers the execution
    of the loading logic until one of the data properties (``dataframe``,
    ``schema``, ``provenance``) is accessed.
    """

    def __init__(
        self,
        id: str,  # noqa: A002
        name: str,
        loader: Callable[[], LoaderResult],
    ) -> None:
        """Initialize a LazyDataset.

        Args:
            id: Unique identifier.
            name: Human-readable name.
            loader: Callable that returns (DataFrame, Schema, Provenance).
        """
        self._id = id
        self._name = name
        self._loader = loader
        self._loaded_data: LoaderResult | None = None
        self.created_at = now_utc()

        # Note: We purposely do NOT call super().__init__ because it requires
        # the dataframe/schema to be present immediately. We override the
        # attributes with properties below.

    @property
    def id(self) -> str:
        """Get dataset ID."""
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        self._id = value

    @property
    def name(self) -> str:
        """Get dataset name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    def _ensure_loaded(self) -> None:
        """Trigger loading if not already loaded."""
        if self._loaded_data is None:
            self._loaded_data = self._loader()

    @property
    def dataframe(self) -> pd.DataFrame:
        """Get the underlying DataFrame (triggering load if needed)."""
        self._ensure_loaded()
        assert self._loaded_data is not None
        return self._loaded_data[0]

    @dataframe.setter
    def dataframe(self, value: pd.DataFrame) -> None:
        """Allow manually setting the dataframe (disables lazy loading)."""
        # If we manually set data, we might have an incosistent state if
        # schema/provenance aren't updated. For now, we assume this is rare.
        # Ideally, we'd update the tuple.
        current_schema = self._loaded_data[1] if self._loaded_data else []
        current_prov = self._loaded_data[2] if self._loaded_data else None

        # We can't really set this safely without the other parts.
        # But to be a polite citizen, if something tries to write to it:
        self._loaded_data = (value, current_schema, current_prov)  # type: ignore

    @property
    def schema(self) -> list[ColumnSchema]:
        """Get the schema (triggering load if needed)."""
        self._ensure_loaded()
        assert self._loaded_data is not None
        return self._loaded_data[1]

    @schema.setter
    def schema(self, value: list[ColumnSchema]) -> None:
        self._ensure_loaded()
        assert self._loaded_data is not None
        self._loaded_data = (self._loaded_data[0], value, self._loaded_data[2])

    @property
    def provenance(self) -> Provenance:
        """Get the provenance (triggering load if needed)."""
        self._ensure_loaded()
        assert self._loaded_data is not None
        return self._loaded_data[2]

    @provenance.setter
    def provenance(self, value: Provenance) -> None:
        self._ensure_loaded()
        assert self._loaded_data is not None
        self._loaded_data = (self._loaded_data[0], self._loaded_data[1], value)
