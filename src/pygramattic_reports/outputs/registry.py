"""Output adapter registry for pygramattic-reports.

Maps format names to output adapter instances so the CLI
and builder can resolve adapters by string name.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseOutputAdapter


class OutputRegistry:
    """Registry of output format adapters.

    Usage::

        registry = create_default_output_registry()
        adapter = registry.get_adapter("docx")
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._adapters: dict[str, BaseOutputAdapter] = {}

    def register(
        self, format_name: str, adapter: BaseOutputAdapter,
    ) -> None:
        """Register an adapter for a format name.

        Args:
            format_name: Short format identifier (e.g. ``"md"``).
            adapter: Adapter instance to use for this format.
        """
        self._adapters[format_name] = adapter

    def get_adapter(self, format_name: str) -> BaseOutputAdapter:
        """Look up an adapter by format name.

        Args:
            format_name: Format identifier.

        Returns:
            The registered adapter.

        Raises:
            ValueError: If no adapter is registered for the format.
        """
        adapter = self._adapters.get(format_name)
        if adapter is None:
            available = ", ".join(sorted(self._adapters))
            msg = (
                f"No adapter for format {format_name!r}. "
                f"Available: {available}"
            )
            raise ValueError(msg)
        return adapter

    def available_formats(self) -> list[str]:
        """Return sorted list of registered format names."""
        return sorted(self._adapters)


def create_default_output_registry() -> OutputRegistry:
    """Create a registry pre-loaded with all built-in adapters.

    Returns:
        Registry with ``md``, ``markdown``, ``docx``, ``xlsx``,
        ``html``, and ``json`` adapters registered.
    """
    from .docx_adapter import DocxAdapter  # noqa: PLC0415
    from .html_adapter import HtmlAdapter  # noqa: PLC0415
    from .json_adapter import JsonAdapter  # noqa: PLC0415
    from .markdown_adapter import MarkdownAdapter  # noqa: PLC0415
    from .xlsx_adapter import XlsxAdapter  # noqa: PLC0415

    registry = OutputRegistry()
    registry.register("md", MarkdownAdapter())
    registry.register("markdown", MarkdownAdapter())
    registry.register("docx", DocxAdapter())
    registry.register("xlsx", XlsxAdapter())
    registry.register("html", HtmlAdapter())
    registry.register("json", JsonAdapter())
    return registry
