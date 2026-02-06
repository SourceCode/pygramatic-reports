"""HTML output adapter for pygramattic-reports."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING

from jinja2 import BaseLoader, Environment

from pygramattic_reports.outputs.base import BaseOutputAdapter
from pygramattic_reports.themes import ThemeApplicator

if TYPE_CHECKING:
    from pygramattic_reports.models import Report, ReportSection, ThemeSpec

# Default template using Theme variables
THEMED_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="generator" content="pygramattic-reports">
    <title>{{ report.name }}</title>
    <style>
        {{ css_styles | safe }}
        
        /* Custom Overrides */
        {{ custom_css | safe }}
    </style>
</head>
<body>
    <div class="report-container">
        
        <!-- Cover Page -->
        {% if report.cover_page %}
        <div class="cover-page page-break">
            <div class="cover-content">
                {% if report.cover_page.logo_path %}
                <img src="{{ report.cover_page.logo_path }}" class="cover-logo" alt="Logo">
                {% endif %}
                <h1 class="cover-title">{{ report.cover_page.title }}</h1>
                {% if report.cover_page.subtitle %}
                <h2 class="cover-subtitle">{{ report.cover_page.subtitle }}</h2>
                {% endif %}
                <div class="cover-meta">
                    {% if report.cover_page.show_date %}
                    <p>{{ report.build_timestamp.strftime('%B %d, %Y') }}</p>
                    {% endif %}
                    {% if report.metadata and report.metadata.version %}
                    <p>Version {{ report.metadata.version }}</p>
                    {% endif %}
                </div>
            </div>
        </div>
        {% else %}
        <!-- Default Title Block if no cover page -->
        <header class="report-header">
            <h1>{{ report.name }}</h1>
            <p class="meta">Generated: {{ report.build_timestamp }}</p>
        </header>
        <hr>
        {% endif %}
        
        <!-- TOC -->
        {% for section in report.sections %}
            {% if section.section_type == 'table_of_contents' %}
                {{ render_toc(report, section) | safe }}
            {% endif %}
        {% endfor %}

        <!-- Content Sections -->
        {% for section in report.sections %}
            {{ render_section(section, loop.index) | safe }}
        {% endfor %}
        
    </div>
</body>
</html>
"""


class HtmlAdapter(BaseOutputAdapter):
    """Renders a Report object to HTML."""

    def render(self, report: Report, theme: ThemeSpec) -> bytes:
        """Render Report to HTML with theme support."""
        # 1. Generate Theme CSS
        applicator = ThemeApplicator(theme)
        css_styles = applicator.to_css_styles()

        # 2. Setup Jinja Env
        env = Environment(loader=BaseLoader(), autoescape=True)

        # 3. Register Helpers
        def b64encode(data: bytes | None) -> str:
            if not data:
                return ""
            return base64.b64encode(data).decode("utf-8")

        env.filters["b64encode"] = b64encode

        # 4. Define Renderers (injected as context or globals)
        # We'll use a macro-like approach by passing a render function

        def render_section(section: ReportSection, index: int) -> str:
            return self._render_section_html(section, index)

        def render_toc(rpt: Report, sec: ReportSection) -> str:
            return self._render_toc_html(rpt, sec)

        # 5. Render Template
        template = env.from_string(THEMED_HTML_TEMPLATE)

        html_str = template.render(
            report=report,
            css_styles=css_styles,
            custom_css="",
            render_section=render_section,
            render_toc=render_toc,
        )

        return html_str.encode("utf-8")

    def _render_section_html(self, section: ReportSection, index: int) -> str:
        """Dispatch render logic for a generic section."""
        st = section.section_type

        # Skip special types handled globally
        if st in ("cover_page", "table_of_contents"):
            return ""

        parts = []
        parts.append(f'<div class="section section-{st}">')

        if st == "page_break":
            parts.append('<div class="page-break"></div>')

        elif st in ("title", "heading"):
            lvl = 1 if st == "title" else min(section.level + 1, 6)
            parts.append(f"<h{lvl}>{section.title or section.content}</h{lvl}>")

        elif st in ("narrative", "summary"):
            if section.title:
                parts.append(f"<h2>{section.title}</h2>")
            if section.content:
                parts.append(f"<div>{section.content}</div>")

        elif st == "chart" or st == "image":
            if section.title:
                parts.append(f"<h3>{section.title}</h3>")
            if section.media_bytes:
                b64 = base64.b64encode(section.media_bytes).decode("utf-8")
                parts.append(
                    f'<img src="data:{section.media_type};base64,{b64}" alt="{section.title}">'
                )

        elif st == "data_table":
            parts.append(self._render_table_html(section))

        elif st == "list":
            parts.append(self._render_list_html(section))

        elif st == "callout":
            parts.append(self._render_callout_html(section))

        elif st == "metric_card":
            # Metric cards usually group together. If singular:
            parts.append('<div class="metric-card-container">')
            parts.append(self._render_metric_card_html(section))
            parts.append("</div>")

        elif st == "code_block":
            parts.append(self._render_code_html(section))

        elif st == "quote":
            parts.append(self._render_quote_html(section))

        elif st == "columns":
            parts.append(self._render_columns_html(section, index))

        parts.append("</div>")
        return "".join(parts)

    def _render_table_html(self, section: ReportSection) -> str:
        if not section.table_data:
            return ""
        headers = section.table_data.get("headers", [])
        rows = section.table_data.get("rows", [])
        totals = section.table_data.get("totals")

        html = []
        if section.title:
            html.append(f"<h3>{section.title}</h3>")
        html.append("<table><thead><tr>")
        for h in headers:
            html.append(f"<th>{h}</th>")
        html.append("</tr></thead>")

        # Footer
        if totals:
            html.append("<tfoot><tr>")
            for cell in totals:
                val = f"{cell:,.2f}" if isinstance(cell, float) else str(cell)
                html.append(f"<td><b>{val}</b></td>")
            html.append("</tr></tfoot>")

        html.append("<tbody>")
        for row in rows:
            html.append("<tr>")
            for cell in row:
                # Conditional Formatting
                cls = ""
                val_str = str(cell)
                if isinstance(cell, (int, float)):
                    if cell < 0:
                        cls = ' class="text-error"'
                    val_str = f"{cell:,.2f}" if isinstance(cell, float) else str(cell)

                html.append(f"<td{cls}>{val_str}</td>")
            html.append("</tr>")
        html.append("</tbody></table>")
        return "".join(html)

    def _render_list_html(self, section: ReportSection) -> str:
        items = section.list_data or []
        html = []
        if section.title:
            html.append(f"<h3>{section.title}</h3>")
        html.append('<ul class="styled-list">')
        for item in items:
            html.append(f"<li>{item}</li>")
        html.append("</ul>")
        return "".join(html)

    def _render_callout_html(self, section: ReportSection) -> str:
        data = section.callout_data or {}
        kind = data.get("type", "info").lower()
        title = section.title or kind.title()
        return f"""
        <div class="callout callout-{kind}">
            <span class="callout-title">{title}</span>
            {data.get("content", "")}
        </div>
        """

    def _render_metric_card_html(self, section: ReportSection) -> str:
        data = section.card_data or {}
        return f"""
        <div class="metric-card">
            <div class="metric-label">{data.get("label", "Metric")}</div>
            <div class="metric-value">{data.get("value", "-")}</div>
        </div>
        """

    def _render_code_html(self, section: ReportSection) -> str:
        data = section.code_data or {}
        if section.title:
            return f"<h3>{section.title}</h3><pre><code>{data.get('code', '')}</code></pre>"
        return f"<pre><code>{data.get('code', '')}</code></pre>"

    def _render_quote_html(self, section: ReportSection) -> str:
        data = section.quote_data or {}
        author_html = (
            f'<div class="quote-author">— {data.get("author")}</div>' if data.get("author") else ""
        )
        return f"""
        <blockquote>
            {data.get("text", "")}
            {author_html}
        </blockquote>
        """

    def _render_columns_html(self, section: ReportSection, index: int) -> str:
        # Check if immediate children are ALL metric cards to group them
        cols = section.columns_data or []
        if not cols:
            return ""

        is_metrics = all(c.section_type == "metric_card" for c in cols)
        container_class = "metric-card-container" if is_metrics else "columns-container"

        html = []
        if section.title:
            html.append(f"<h2>{section.title}</h2>")

        html.append(f'<div class="{container_class}">')
        for i, col in enumerate(cols):
            # For metrics in a group, bypass wrapping div overhead
            if is_metrics:
                html.append(self._render_metric_card_html(col))
            else:
                # Recursive render for generic columns
                # We wrap in a column div to protect layout
                html.append(
                    f'<div class="column-item">{self._render_section_html(col, index + 100 + i)}</div>'
                )
        html.append("</div>")
        return "".join(html)

    def _render_toc_html(self, report: Report, section: ReportSection) -> str:
        html = ['<nav class="toc">']
        if section.title:
            html.append(f"<h2>{section.title}</h2>")
        html.append("<ul>")
        for s in report.sections:
            if s.section_type in ("title", "heading") and s.title:
                # Generating IDs is tricky without a pass, assume linear for now or js
                # Simplified: just list them
                html.append(f'<li class="toc-level-{s.level}">{s.title}</li>')
        html.append("</ul></nav>")
        return "".join(html)

    def file_extension(self) -> str:
        """Return the file extension."""
        return ".html"
