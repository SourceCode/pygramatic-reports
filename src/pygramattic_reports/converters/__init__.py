"""Data format converters.

Convert Dataset objects to various output formats.

Usage::

    from pygramattic_reports.converters import to_json, to_sql, to_csv

    json_str = to_json(dataset)
    sql_str = to_sql(dataset, dialect="postgresql")
    csv_str = to_csv(dataset)
"""

from .csv_converter import to_csv
from .json_converter import to_json
from .sql_converter import to_sql

__all__ = ["to_csv", "to_json", "to_sql"]
