"""Data processing functions (spreadsheet-like operations).

Usage::

    from pygramattic_reports.processors import aggregate, filter_rows
"""

from .functions import (
    aggregate,
    filter_rows,
    moving_average,
    percent_change,
    ratio,
    running_total,
)

__all__ = [
    "aggregate",
    "filter_rows",
    "moving_average",
    "percent_change",
    "ratio",
    "running_total",
]
