"""Validation result models for pygramattic-reports.

Defines the output model for the Validator module.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class CheckStatus(StrEnum):
    """Status of a single validation check."""

    PASS = "pass"  # noqa: S105
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


class ValidationCheck(BaseModel):
    """A single validation check result.

    Attributes:
        check_name: Name of the check performed.
        status: Check outcome.
        message: Human-readable result message.
        expected: Expected value as string.
        actual: Actual value as string.
        section_index: Which report section was checked.
        severity: Severity level of the check.
    """

    model_config = ConfigDict(frozen=True)

    check_name: str
    status: CheckStatus
    message: str
    expected: str | None = None
    actual: str | None = None
    section_index: int | None = None
    severity: str = "error"


class ValidationResult(BaseModel):
    """Complete validation report.

    Attributes:
        report_id: ID of the report that was validated.
        overall_status: Aggregate status across all checks.
        checks: Individual check results.
        total_checks: Total number of checks performed.
        passed: Number of checks that passed.
        failed: Number of checks that failed.
        warnings: Number of checks with warnings.
        validated_at: When validation was performed.
    """

    model_config = ConfigDict(frozen=True)

    report_id: str
    overall_status: CheckStatus
    checks: list[ValidationCheck]
    total_checks: int
    passed: int
    failed: int
    warnings: int
    validated_at: datetime
