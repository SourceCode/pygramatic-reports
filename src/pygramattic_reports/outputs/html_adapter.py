"""HTML output adapter for pygramattic-reports."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING

from jinja2 import BaseLoader, Environment

from pygramattic_reports.outputs.base import BaseOutputAdapter

if TYPE_CHECKING:
    from pygramattic_reports.models import Report, ThemeSpec

# Minimal default template if no theme provided or for fallback
DEFAULT_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report.name }}</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; }
        .section { margin-bottom: 2rem; }
        img { max-width: 100%; height: auto; }
        table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>{{ report.name }}</h1>
    <p>Generated on: {{ report.build_timestamp }}</p>
    <hr>
    
    {% for section in report.sections %}
        <div class="section">
        {% if section.section_type == 'title' %}
            <h1 style="text-align: center;">{{ section.content }}</h1>
        
        {% elif section.section_type in ['heading', 'narrative', 'summary'] %}
            {% if section.title %}
                <h{{ section.level + 1 }}>{{ section.title }}</h{{ section.level + 1 }}>
            {% endif %}
            {% if section.content %}
                <div>{{ section.content | safe }}</div>
            {% endif %}

        {% elif section.section_type == 'data_table' %}
            {% if section.title %}<h3>{{ section.title }}</h3>{% endif %}
            {% if section.table_data %}
            <table>
                <thead>
                    <tr>
                    {% for col in section.table_data.headers %}
                        <th>{{ col }}</th>
                    {% endfor %}
                    </tr>
                </thead>
                <tbody>
                    {% for row in section.table_data.rows %}
                    <tr>
                        {% for cell in row %}
                        <td>{{ cell }}</td>
                        {% endfor %}
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}

        {% elif section.section_type in ['chart', 'image'] %}
            {% if section.title %}<h3>{{ section.title }}</h3>{% endif %}
            {% if section.media_bytes %}
                <img src="data:{{ section.media_type }};base64,{{ section.media_bytes | b64encode }}" 
                     alt="{{ section.title or 'Image' }}">
            {% endif %}
            
        {% elif section.section_type == 'page_break' %}
            <hr style="border-top: 2px dashed #ccc; margin: 4rem 0;">

        {% endif %}
        </div>
    {% endfor %}
</body>
</html>
"""

class HtmlAdapter(BaseOutputAdapter):
    """Renders a Report object to HTML."""

    def render(self, report: Report, _theme: ThemeSpec) -> bytes:
        """Render Report to HTML.

        Args:
            report: The abstract report to render.
            _theme: Theme for styling (currently uses default template, theme support TODO).

        Returns:
            HTML string encoded as bytes.
        """
        # Create a Jinja2 environment from the string template
        # In the future, this should load from theme.template_path
        env = Environment(loader=BaseLoader(), autoescape=True)
        template = env.from_string(DEFAULT_HTML_TEMPLATE)

        # Helper filter for base64 encoding
        def b64encode(data: bytes | None) -> str:
            if not data:
                return ""
            return base64.b64encode(data).decode("utf-8")

        env.filters["b64encode"] = b64encode

        html_str = template.render(report=report)
        return html_str.encode("utf-8")

    def file_extension(self) -> str:
        """Return the file extension."""
        return ".html"
