"""Spreadsheet-like data processing functions.

Aggregations, filters, window functions, percent change, and ratios
that can be used in templates and by the builder to compute derived
values from datasets.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from pygramattic_reports.models import Dataset

_VALID_OPERATIONS = frozenset({"sum", "avg", "min", "max", "count"})
_VALID_OPERATORS = frozenset({
    "eq", "ne", "gt", "gte", "lt", "lte", "contains",
})


def aggregate(
    dataset: Dataset, column: str, operation: str,
) -> float:
    """Compute an aggregate over a dataset column.

    Args:
        dataset: Source dataset.
        column: Column name.
        operation: One of ``"sum"``, ``"avg"``, ``"min"``,
            ``"max"``, ``"count"``.

    Returns:
        Computed aggregate value.

    Raises:
        ValueError: If operation is unknown.
    """
    if operation not in _VALID_OPERATIONS:
        msg = f"Unknown operation: {operation!r}"
        raise ValueError(msg)
    series = dataset.dataframe[column]
    if operation == "sum":
        return float(series.sum())
    if operation == "avg":
        return float(series.mean())
    if operation == "min":
        return float(series.min())
    if operation == "max":
        return float(series.max())
    # count
    return float(series.count())


def filter_rows(
    dataset: Dataset,
    column: str,
    operator: str,
    value: object,
) -> pd.DataFrame:
    """Filter dataset rows by a condition.

    Args:
        dataset: Source dataset.
        column: Column to filter on.
        operator: Comparison operator (``"eq"``, ``"ne"``, ``"gt"``,
            ``"gte"``, ``"lt"``, ``"lte"``, ``"contains"``).
        value: Comparison value.

    Returns:
        Filtered DataFrame.

    Raises:
        ValueError: If operator is unknown.
    """
    if operator not in _VALID_OPERATORS:
        msg = f"Unknown operator: {operator!r}"
        raise ValueError(msg)

    df = dataset.dataframe
    col = df[column]

    if operator == "eq":
        mask = col == value
    elif operator == "ne":
        mask = col != value
    elif operator == "gt":
        mask = col > value
    elif operator == "gte":
        mask = col >= value
    elif operator == "lt":
        mask = col < value
    elif operator == "lte":
        mask = col <= value
    else:
        # contains
        mask = col.astype(str).str.contains(str(value), na=False)

    return df[mask]


def percent_change(
    dataset: Dataset, column: str, periods: int = 1,
) -> pd.Series:
    """Compute percent change over periods for a column.

    Args:
        dataset: Source dataset.
        column: Column name.
        periods: Number of periods to shift.

    Returns:
        Series of percent changes.
    """
    return dataset.dataframe[column].pct_change(periods=periods)


def ratio(
    dataset: Dataset,
    numerator_col: str,
    denominator_col: str,
) -> pd.Series:
    """Compute ratio of two columns.

    Args:
        dataset: Source dataset.
        numerator_col: Numerator column name.
        denominator_col: Denominator column name.

    Returns:
        Series of ratios.
    """
    df = dataset.dataframe
    return df[numerator_col] / df[denominator_col]


def running_total(dataset: Dataset, column: str) -> pd.Series:
    """Compute running total (cumulative sum) of a column.

    Args:
        dataset: Source dataset.
        column: Column name.

    Returns:
        Series of cumulative sums.
    """
    return dataset.dataframe[column].cumsum()


def moving_average(
    dataset: Dataset, column: str, window: int = 3,
) -> pd.Series:
    """Compute moving average of a column.

    Args:
        dataset: Source dataset.
        column: Column name.
        window: Rolling window size.

    Returns:
        Series of moving averages.
    """
    return dataset.dataframe[column].rolling(window=window).mean()
