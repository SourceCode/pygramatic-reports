"""Numerical validation for generated reports.

Deterministic validation that cross-checks numerical claims in
reports against source datasets. No AI required.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from pygramattic_reports.models import (
    CheckStatus,
    ValidationCheck,
)
from pygramattic_reports.processors import aggregate

if TYPE_CHECKING:
    from pygramattic_reports.models import Dataset, NumberClaim, Report


class NumericalValidator:
    """Validates numerical claims in reports against source data.

    Uses the NumberClaim manifest from the Builder to deterministically
    verify every number in the report. This does NOT use AI — it is
    pure programmatic comparison.

    Checks:

    - Each NumberClaim's value matches the source dataset
    - Computed values (sums, averages) are correct
    - No NaN or infinite values in claims
    """

    def __init__(self, tolerance: float = 0.01) -> None:
        """Initialize with comparison tolerance.

        Args:
            tolerance: Relative tolerance for float comparison (1% default).
        """
        self.tolerance = tolerance

    def validate(
        self,
        report: Report,
        datasets: dict[str, Dataset],
    ) -> list[ValidationCheck]:
        """Validate all numerical claims.

        Args:
            report: The report to validate.
            datasets: Map of dataset_id -> Dataset for source verification.

        Returns:
            List of ValidationCheck results.
        """
        return [self._verify_claim(claim, datasets) for claim in report.number_claims]

    def _verify_claim(
        self,
        claim: NumberClaim,
        datasets: dict[str, Dataset],
    ) -> ValidationCheck:
        """Verify a single numerical claim against source data."""
        dataset = datasets.get(claim.source_dataset_id)
        if dataset is None:
            return ValidationCheck(
                check_name=f"number_claim_{claim.description}",
                status=CheckStatus.SKIP,
                message=(f"Source dataset {claim.source_dataset_id} not found"),
                section_index=claim.section_index,
            )

        if math.isnan(claim.value) or math.isinf(claim.value):
            return ValidationCheck(
                check_name=f"number_claim_{claim.description}",
                status=CheckStatus.WARN,
                message=f"{claim.description}: value is NaN/Inf",
                section_index=claim.section_index,
                severity="warning",
            )

        try:
            expected = self._compute_expected(claim, dataset)
        except Exception as exc:
            return ValidationCheck(
                check_name=f"number_claim_{claim.description}",
                status=CheckStatus.WARN,
                message=f"Could not verify: {exc}",
                section_index=claim.section_index,
                severity="warning",
            )

        if self._values_match(claim.value, expected):
            return ValidationCheck(
                check_name=f"number_claim_{claim.description}",
                status=CheckStatus.PASS,
                message=(f"{claim.description}: {claim.formatted_value} matches source"),
                expected=str(expected),
                actual=str(claim.value),
                section_index=claim.section_index,
            )
        return ValidationCheck(
            check_name=f"number_claim_{claim.description}",
            status=CheckStatus.FAIL,
            message=(f"{claim.description}: expected {expected}, got {claim.value}"),
            expected=str(expected),
            actual=str(claim.value),
            section_index=claim.section_index,
        )

    @staticmethod
    def _compute_expected(
        claim: NumberClaim,
        dataset: Dataset,
    ) -> float:
        """Re-compute the expected value from the source dataset."""
        if claim.computation.startswith("raw["):
            row_idx = int(claim.computation.split("[")[1].rstrip("]"))
            return float(dataset.dataframe[claim.source_column].iloc[row_idx])
        if claim.computation in ("sum", "avg", "min", "max", "count"):
            return aggregate(dataset, claim.source_column, claim.computation)
        msg = f"Unknown computation: {claim.computation}"
        raise ValueError(msg)

    def _values_match(self, actual: float, expected: float) -> bool:
        """Compare two float values with tolerance."""
        if expected == 0:
            return abs(actual) < self.tolerance
        return abs((actual - expected) / expected) < self.tolerance
