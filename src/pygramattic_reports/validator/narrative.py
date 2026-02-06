"""AI-assisted narrative validation for generated reports.

Uses Claude CLI to check narrative sections for factual
alignment with source data. Optional — skips if AI is unavailable.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pygramattic_reports.ai.prompts import VALIDATION_PROMPT
from pygramattic_reports.exceptions import AIError
from pygramattic_reports.logging import get_logger
from pygramattic_reports.models import (
    CheckStatus,
    SectionType,
    ValidationCheck,
)

if TYPE_CHECKING:
    from pygramattic_reports.ai import ClaudeClient
    from pygramattic_reports.models import Dataset, Report, ReportSection

logger = get_logger("validator.narrative")


class NarrativeValidator:
    """AI-assisted validation of narrative report sections.

    Uses Claude CLI to check whether narrative text accurately
    reflects the underlying data. This is optional — if AI is
    unavailable, narrative validation is skipped.
    """

    def __init__(self, client: ClaudeClient | None) -> None:
        """Initialize with optional Claude client.

        Args:
            client: Claude CLI client, or None to skip AI validation.
        """
        self.client = client

    def validate(
        self,
        report: Report,
        datasets: dict[str, Dataset],
    ) -> list[ValidationCheck]:
        """Validate narrative sections using AI.

        Skips validation if Claude CLI is unavailable.

        Args:
            report: The report to validate.
            datasets: Named datasets for context.

        Returns:
            List of ValidationCheck results.
        """
        if self.client is None or not self.client.is_available():
            return [
                ValidationCheck(
                    check_name="narrative_validation",
                    status=CheckStatus.SKIP,
                    message="Narrative validation skipped: AI unavailable",
                ),
            ]

        checks: list[ValidationCheck] = []
        for i, section in enumerate(report.sections):
            if section.section_type in (
                SectionType.SUMMARY,
                SectionType.NARRATIVE,
            ):
                checks.append(
                    self._validate_section(section, i, datasets),
                )
        return checks

    def _validate_section(
        self,
        section: ReportSection,
        index: int,
        datasets: dict[str, Dataset],
    ) -> ValidationCheck:
        """Validate a single narrative section."""
        data_summary = "\n".join(
            f"{name}: {ds.dataframe.describe().to_string()}"
            for name, ds in datasets.items()
        )

        prompt = VALIDATION_PROMPT.format(
            report_text=section.content or "",
            source_data=data_summary,
        )

        try:
            response = self.client.generate(prompt=prompt)  # type: ignore[union-attr]
            result = json.loads(response)
            valid = result.get("valid", True)
            issues: list[str] = result.get("issues", [])
        except (AIError, json.JSONDecodeError) as exc:
            logger.warning(
                "Narrative validation failed",
                section_index=index,
                error=str(exc),
            )
            return ValidationCheck(
                check_name=f"narrative_accuracy_{index}",
                status=CheckStatus.SKIP,
                message=f"Narrative validation failed: {exc}",
                section_index=index,
            )

        if valid:
            return ValidationCheck(
                check_name=f"narrative_accuracy_{index}",
                status=CheckStatus.PASS,
                message=(
                    f"Narrative section {index} is consistent with data"
                ),
                section_index=index,
            )
        return ValidationCheck(
            check_name=f"narrative_accuracy_{index}",
            status=CheckStatus.WARN,
            message=f"Narrative issues: {'; '.join(issues)}",
            section_index=index,
            severity="warning",
        )
