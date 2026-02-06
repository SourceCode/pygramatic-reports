"""Report validation orchestrator.

Runs three layers of validation and produces a
complete ``ValidationResult``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygramattic_reports.models import CheckStatus, ValidationResult
from pygramattic_reports.models.base import now_utc

from .narrative import NarrativeValidator
from .numerical import NumericalValidator
from .structural import StructuralValidator

if TYPE_CHECKING:
    from pygramattic_reports.ai import ClaudeClient
    from pygramattic_reports.models import Dataset, Report, TemplateSpec


class ReportValidator:
    """Full report validation orchestrator.

    Runs three layers of validation:

    1. Structural: template compliance, section completeness
    2. Numerical: data accuracy, computation correctness
    3. Narrative: AI-assisted factual alignment (optional)

    Usage::

        validator = ReportValidator(claude_client=client)
        result = validator.validate(report, template, datasets)
        if result.overall_status == CheckStatus.FAIL:
            for check in result.checks:
                if check.status == CheckStatus.FAIL:
                    print(f"  - {check.message}")
    """

    def __init__(self, claude_client: ClaudeClient | None = None) -> None:
        """Initialize with optional AI client.

        Args:
            claude_client: Claude CLI client for narrative validation,
                or None to skip AI-based checks.
        """
        self.structural = StructuralValidator()
        self.numerical = NumericalValidator()
        self.narrative = NarrativeValidator(claude_client)

    def validate(
        self,
        report: Report,
        template: TemplateSpec,
        datasets: dict[str, Dataset],
    ) -> ValidationResult:
        """Run all validation checks and produce a ValidationResult.

        Args:
            report: The generated report.
            template: The template it was built from.
            datasets: Named datasets used by the report.

        Returns:
            Complete ValidationResult with all checks.
        """
        all_checks = []

        all_checks.extend(self.structural.validate(report, template))

        dataset_by_id = {ds.id: ds for ds in datasets.values()}
        all_checks.extend(self.numerical.validate(report, dataset_by_id))

        all_checks.extend(self.narrative.validate(report, datasets))

        passed = sum(1 for c in all_checks if c.status == CheckStatus.PASS)
        failed = sum(1 for c in all_checks if c.status == CheckStatus.FAIL)
        warnings = sum(1 for c in all_checks if c.status == CheckStatus.WARN)

        if failed > 0:
            overall = CheckStatus.FAIL
        elif warnings > 0:
            overall = CheckStatus.WARN
        else:
            overall = CheckStatus.PASS

        return ValidationResult(
            report_id=report.id,
            overall_status=overall,
            checks=all_checks,
            total_checks=len(all_checks),
            passed=passed,
            failed=failed,
            warnings=warnings,
            validated_at=now_utc(),
        )
