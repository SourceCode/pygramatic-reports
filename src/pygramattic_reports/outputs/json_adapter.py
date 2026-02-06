"""JSON output adapter for pygramattic-reports."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygramattic_reports.outputs.base import BaseOutputAdapter

if TYPE_CHECKING:
    from pygramattic_reports.models import Report, ThemeSpec


class JsonAdapter(BaseOutputAdapter):
    """Renders a Report object to a JSON file."""

    def render(self, report: Report, _theme: ThemeSpec) -> bytes:
        """Render Report to JSON.

        Args:
            report: The abstract report to render.
            theme: Ignored for JSON output.

        Returns:
            JSON string encoded as bytes.
        """
        # Pydantic's model_dump_json handles serialization of the entire object graph
        json_str = report.model_dump_json(indent=2)
        return json_str.encode("utf-8")

    def file_extension(self) -> str:
        """Return the file extension."""
        return ".json"
