"""Data processing engine for pygramattic-reports.

Handles filtering, sorting, aggregation, and transformation of Datasets
based on TemplateSectionSpec configurations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

from pygramattic_reports.exceptions import DataError
from pygramattic_reports.logging import get_logger

if TYPE_CHECKING:
    from pygramattic_reports.models import Dataset, TemplateSectionSpec


_logger = get_logger("processors.data")


class DataProcessor:
    """Processes datasets based on section specifications."""

    def process(
        self,
        dataset: Dataset,
        spec: TemplateSectionSpec,
        other_datasets: dict[str, Dataset] | None = None,
    ) -> pd.DataFrame:
        """Apply all transformations defined in the spec to the dataset.

        Args:
            dataset: The source dataset.
            spec: The section specification containing data operations.
            other_datasets: Optional map of all available datasets (needed for joins).

        Returns:
            A transformed DataFrame (copy).
        """
        df = dataset.dataframe.copy()

        # 0. Joins (Before everything, to bring in data)
        if spec.joins:
            if not other_datasets:
                _logger.warning("Joins requested but no other datasets provided.")
            else:
                df = self._apply_joins(df, spec.joins, other_datasets)

        # 0.5. Validation (After joining, before other processing)
        if spec.validation_rules:
            self._validate_data(df, spec.validation_rules)

        # 1. Calculated Columns
        if spec.calculated_columns:
            df = self._apply_calculations(df, spec.calculated_columns)

        # 2. Filtering
        if spec.filters:
            df = self._apply_filters(df, spec.filters)

        # 3. Grouping & Aggregation
        if spec.group_by:
            # If grouping is used, it replaces the dataframe with the aggregated result
            df = self._apply_grouping(df, spec.group_by, spec.aggregations)

        # 4. Sorting (Post-aggregation if grouped)
        if spec.sort:
            df = self._apply_sorting(df, spec.sort)

        # 5. Limiting
        if spec.limit is not None:
            df = df.head(spec.limit)

        # 6. Column Selection (Final projection)
        # Note: If grouped, columns might have changed.
        # Only apply if not grouped, or if columns exist in result.
        if spec.columns and not spec.group_by:
            missing = [c for c in spec.columns if c not in df.columns]
            if missing:
                # Be convenient: skip missing columns or error?
                # For now, let's warn and skip to avoid crashing
                _logger.warning("Requested columns not found", missing=missing)
                cols_to_use = [c for c in spec.columns if c in df.columns]
                if cols_to_use:
                    df = df[cols_to_use]
            else:
                df = df[spec.columns]

        return df

    def _apply_joins(
        self,
        df: pd.DataFrame,
        joins: list[dict[str, Any]],
        other_datasets: dict[str, Dataset],
    ) -> pd.DataFrame:
        """Apply dataset joins."""
        for j in joins:
            target_name = j.get("dataset")
            if not target_name or target_name not in other_datasets:
                _logger.warning("Join target not found", target=target_name)
                continue

            target_ds = other_datasets[target_name]
            target_df = target_ds.dataframe

            # Join parameters
            how = j.get("how", "left")
            on = j.get("on")
            left_on = j.get("left_on") or on
            right_on = j.get("right_on") or on
            suffixes = tuple(j.get("suffixes", ("_x", "_y")))

            try:
                df = pd.merge(
                    df,
                    target_df,
                    how=how,
                    left_on=left_on,
                    right_on=right_on,
                    suffixes=suffixes,
                )
            except Exception as exc:
                _logger.error(
                    "Join failed",
                    target=target_name,
                    error=str(exc),
                )
        return df

    def _validate_data(self, df: pd.DataFrame, rules: list[dict[str, Any]]) -> None:
        """Validate data against rules."""
        for rule in rules:
            rule_type = rule.get("type")
            col = rule.get("col")
            level = rule.get("level", "warning")  # warning or error

            if not col or col not in df.columns:
                continue

            failed_rows = 0
            msg = ""

            try:
                if rule_type == "completeness":
                    # Check for nulls
                    failed = df[col].isna()
                    failed_rows = failed.sum()
                    msg = f"Column '{col}' has {failed_rows} missing values"

                elif rule_type == "unique":
                    # Check for duplicates
                    if not df[col].is_unique:
                        failed_rows = df.duplicated(subset=[col]).sum()
                        msg = f"Column '{col}' has {failed_rows} duplicate values"

                elif rule_type == "range":
                    # Check min/max
                    min_val = rule.get("min")
                    max_val = rule.get("max")

                    if min_val is not None:
                        failed = df[col] < min_val
                        failed_rows += failed.sum()
                    if max_val is not None:
                        failed = df[col] > max_val
                        failed_rows += failed.sum()

                    if failed_rows > 0:
                        msg = f"Column '{col}' has values outside range [{min_val}, {max_val}]"

                if failed_rows > 0:
                    if level == "error":
                        _logger.error("Data Validation Error", message=msg)
                        raise DataError(msg)
                    _logger.warning("Data Validation Warning", message=msg)

            except Exception as exc:
                if isinstance(exc, DataError):
                    raise
                _logger.warning("Validation rule failed execution", rule=rule, error=str(exc))

    def _apply_calculations(
        self,
        df: pd.DataFrame,
        calculations: dict[str, str],
    ) -> pd.DataFrame:
        """Add calculated columns using pandas eval."""
        for name, expr in calculations.items():
            try:
                # Use query/eval for safety
                # Note: This allows arbitrary code execution if not careful.
                # In a robust system, we'd use a restricted parser.
                # For now, assuming internal templates are trusted.
                df[name] = df.eval(expr)
            except Exception as exc:
                _logger.warning(
                    "Calculation failed",
                    column=name,
                    expression=expr,
                    error=str(exc),
                )
        return df

    def _apply_filters(
        self,
        df: pd.DataFrame,
        filters: list[dict[str, Any]],
    ) -> pd.DataFrame:
        """Apply row filters."""
        for f in filters:
            col = f.get("col")
            op = f.get("op", "eq")
            val = f.get("val")

            if not col or col not in df.columns:
                continue

            try:
                if op == "eq":
                    df = df[df[col] == val]
                elif op == "neq":
                    df = df[df[col] != val]
                elif op == "gt":
                    df = df[df[col] > val]
                elif op == "gte":
                    df = df[df[col] >= val]
                elif op == "lt":
                    df = df[df[col] < val]
                elif op == "lte":
                    df = df[df[col] <= val]
                elif op == "in":
                    df = df[df[col].isin(val if isinstance(val, list) else [val])]
                elif op == "contains":
                    df = df[df[col].astype(str).str.contains(str(val), case=False, na=False)]
            except Exception as exc:
                _logger.warning(
                    "Filter failed",
                    filter=f,
                    error=str(exc),
                )
        return df

    def _apply_sorting(self, df: pd.DataFrame, sort_cols: list[str]) -> pd.DataFrame:
        """Apply sorting."""
        cols = []
        ascending = []

        for col in sort_cols:
            if col.startswith("-"):
                name = col[1:]
                if name in df.columns:
                    cols.append(name)
                    ascending.append(False)
            elif col in df.columns:
                cols.append(col)
                ascending.append(True)

        if cols:
            df = df.sort_values(by=cols, ascending=ascending)

        return df

    def _apply_grouping(
        self, df: pd.DataFrame, group_by: list[str], aggregations: dict[str, str] | None
    ) -> pd.DataFrame:
        """Apply group by and aggregation."""
        valid_groups = [c for c in group_by if c in df.columns]
        if not valid_groups:
            return df

        agg_map = aggregations or {}
        # If no aggregations specified, just return unique groups?
        # Or default to count?
        if not agg_map:
            # Just return uniques of the group columns
            return df[valid_groups].drop_duplicates()

        try:
            # Pandas groupby agg needs dict like {'col': 'sum'}
            grouped = df.groupby(valid_groups).agg(agg_map).reset_index()
            return grouped
        except Exception as exc:
            _logger.error("Grouping failed", error=str(exc))
            raise DataError(f"Grouping failed: {exc}") from exc
