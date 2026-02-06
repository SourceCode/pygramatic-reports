"""Data loaders for reading files and databases.

Usage::

    from pygramattic_reports.loaders import create_default_registry

    registry = create_default_registry()
    loader = registry.get_loader(SourceType.CSV)
    raw_data = loader.load(source_config)
"""

from .csv_loader import CsvLoader
from .docx_loader import DocxLoader
from .json_loader import JsonLoader
from .md_loader import MdLoader
from .registry import LoaderRegistry
from .txt_loader import TxtLoader
from .xlsx_loader import XlsxLoader


def create_default_registry() -> LoaderRegistry:
    """Create a LoaderRegistry with all built-in loaders registered."""
    registry = LoaderRegistry()
    registry.register(CsvLoader())
    registry.register(JsonLoader())
    registry.register(XlsxLoader())
    registry.register(DocxLoader())
    registry.register(TxtLoader())
    registry.register(MdLoader())
    return registry


__all__ = [
    "CsvLoader",
    "DocxLoader",
    "JsonLoader",
    "LoaderRegistry",
    "MdLoader",
    "TxtLoader",
    "XlsxLoader",
    "create_default_registry",
]
