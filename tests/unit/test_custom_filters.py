"""Tests for custom Jinja2 filters."""

from datetime import datetime

from pygramattic_reports.templates.renderer import TemplateRenderer


def test_custom_filters():
    renderer = TemplateRenderer()

    # Test Currency
    assert renderer.render_string("{{ 1234.56 | currency }}", {}) == "$1,234.56"
    assert renderer.render_string("{{ 100 | currency(symbol='€') }}", {}) == "€100.00"

    # Test Percent
    assert renderer.render_string("{{ 0.5678 | percent }}", {}) == "56.8%"
    assert renderer.render_string("{{ 0.123 | percent(decimals=2) }}", {}) == "12.30%"

    # Test Date
    dt = datetime(2023, 12, 25)
    assert renderer.render_string("{{ val | date }}", {"val": dt}) == "2023-12-25"
    assert renderer.render_string("{{ val | date(format='%b %Y') }}", {"val": dt}) == "Dec 2023"
    assert (
        renderer.render_string("{{ '2023-01-01' | date }}", {}) == "2023-01-01"
    )  # ISO string passthrough

    # Test Number
    assert renderer.render_string("{{ 1234567 | number }}", {}) == "1,234,567.00"
    assert renderer.render_string("{{ 1234 | number(decimals=0) }}", {}) == "1,234"
