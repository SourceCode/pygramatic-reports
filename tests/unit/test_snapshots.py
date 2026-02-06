"""Snapshot tests for Pygramattic Reports."""

import pandas as pd
import pytest
from syrupy.extensions.single_file import SingleFileSnapshotExtension

from pygramattic_reports.api import Pygramattic


class HTMLSnapshotExtension(SingleFileSnapshotExtension):
    """Extension to handle HTML file snapshots."""

    _file_extension = "html"

    def serialize(self, data: str, **kwargs) -> bytes:
        return data.encode("utf-8")


import re

def sanitize_html(html: str) -> str:
    """Sanitize HTML content by masking dynamic values."""
    # Mask UUIDs
    html = re.sub(
        r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        '00000000-0000-0000-0000-000000000000',
        html
    )
    # Mask ISO timestamps (e.g., 2024-02-06T12:00:00.000000)
    html = re.sub(
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?',
        '2000-01-01T00:00:00',
        html
    )
    # Mask Footer "Generated at" dates specifically if they differ format
    # (Assuming ISO mostly, but keep an eye out)
    return html

@pytest.fixture
def snapshot_html(snapshot):
    """Fixture that uses HTML extension."""
    return snapshot.use_extension(HTMLSnapshotExtension)


def test_report_html_snapshot(snapshot_html, tmp_path):
    """Verify that the generated HTML report matches the snapshot."""

    # Create sample data
    df = pd.DataFrame(
        {
            "Region": ["North", "South", "East", "West"],
            "Sales": [100, 150, 80, 120],
            "Profit": [20, 30, 15, 25],
        }
    )

    # Build a report using the fluent API
    report = (
        Pygramattic()
        .configure(
            title="Snapshot Test Report",
            author="Test Bot",
            subject="Regression Testing",
            keywords=["test", "snapshot"],
        )
        .add_dataset("sales_data", df)
        .add_section(
            title="Executive Summary",
            content="This is a test report to verify HTML output consistency.",
            level=1,
        )
        .add_chart(
            title="Regional Sales",
            dataset="sales_data",
            chart_type="bar",
            x_col="Region",
            y_cols=["Sales"],
            description="Sales performance by region.",
        )
        .build()
    )

    # Render to HTML string
    # We use a temporary file to save, then read it back
    output_path = tmp_path / "report.html"
    report.save(str(output_path))

    content = output_path.read_text(encoding="utf-8")

    # Sanitize content (remove dynamic dates/IDs if necessary)
    sanitized_content = sanitize_html(content)

    assert sanitized_content == snapshot_html
