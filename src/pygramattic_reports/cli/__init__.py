"""Command-line interface for pygramattic-reports.

Usage::

    report ingest data.csv
    report list datasets
    report init
    report build config.yaml
"""

from .main import app

__all__ = ["app"]
