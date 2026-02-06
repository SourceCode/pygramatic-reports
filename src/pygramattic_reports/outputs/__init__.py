"""Output format adapters for pygramattic-reports.

Convert abstract Report objects to format-specific documents.

Usage::

    from pygramattic_reports.outputs import MarkdownAdapter, DocxAdapter, XlsxAdapter

    adapter = MarkdownAdapter(media_dir=Path("media/"))
    adapter.save(report, theme, Path("report.md"))
"""

from .base import BaseOutputAdapter
from .docx_adapter import DocxAdapter
from .html_adapter import HtmlAdapter
from .json_adapter import JsonAdapter
from .markdown_adapter import MarkdownAdapter
from .registry import OutputRegistry, create_default_output_registry
from .xlsx_adapter import XlsxAdapter

__all__ = [
    "BaseOutputAdapter",
    "DocxAdapter",
    "HtmlAdapter",
    "JsonAdapter",
    "MarkdownAdapter",
    "OutputRegistry",
    "XlsxAdapter",
    "create_default_output_registry",
]
