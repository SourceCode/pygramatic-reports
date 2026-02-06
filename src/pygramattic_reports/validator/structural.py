"""Structural validation for generated reports.

Deterministic checks verifying report structure and completeness
against the source template — no AI required.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygramattic_reports.models import (
    CheckStatus,
    SectionType,
    ValidationCheck,
)

if TYPE_CHECKING:
    from pygramattic_reports.models import Report, TemplateSpec


class StructuralValidator:
    """Validates report structure against the template.

    Checks:

    - All required sections from the template are present
    - Data table sections contain data (non-empty headers and rows)
    - Chart sections contain image data
    - No sections are missing titles where required
    - Section ordering matches template
    """

    def validate(
        self,
        report: Report,
        template: TemplateSpec,
    ) -> list[ValidationCheck]:
        """Run all structural validation checks.

        Args:
            report: The generated report.
            template: The template it was built from.

        Returns:
            List of ValidationCheck results.
        """
        checks: list[ValidationCheck] = []
        checks.extend(self._check_section_count(report, template))
        checks.extend(self._check_section_types(report, template))
        checks.extend(self._check_data_tables(report))
        checks.extend(self._check_charts(report))
        checks.extend(self._check_titles(report))
        return checks

    @staticmethod
    def _check_section_count(
        report: Report,
        template: TemplateSpec,
    ) -> list[ValidationCheck]:
        """Verify the expected number of sections were generated."""
        expected = len(template.sections)
        actual = len(report.sections)
        min_expected = expected - len(report.build_warnings)
        status = CheckStatus.PASS if actual >= min_expected else CheckStatus.FAIL
        return [
            ValidationCheck(
                check_name="section_count",
                status=status,
                message=f"Expected ~{expected} sections, got {actual}",
                expected=str(expected),
                actual=str(actual),
            ),
        ]

    @staticmethod
    def _check_section_types(
        report: Report,
        template: TemplateSpec,
    ) -> list[ValidationCheck]:
        """Verify section types match template expectations."""
        from pygramattic_reports.builder.section_processors import map_section_type  # noqa: PLC0415

        checks: list[ValidationCheck] = []
        for i, tpl_section in enumerate(template.sections):
            expected_type = map_section_type(tpl_section.type)
            if i < len(report.sections):
                actual_type = report.sections[i].section_type
                match = actual_type == expected_type
                checks.append(
                    ValidationCheck(
                        check_name=f"section_type_{i}",
                        status=CheckStatus.PASS if match else CheckStatus.WARN,
                        message=(
                            f"Section {i}: expected {expected_type.value}, "
                            f"got {actual_type.value}"
                        ),
                        expected=expected_type.value,
                        actual=actual_type.value,
                        section_index=i,
                    ),
                )
        return checks

    @staticmethod
    def _check_data_tables(report: Report) -> list[ValidationCheck]:
        """Verify data table sections have content."""
        checks: list[ValidationCheck] = []
        for i, section in enumerate(report.sections):
            if section.section_type == SectionType.DATA_TABLE:
                has_data = (
                    section.table_data is not None
                    and len(section.table_data.get("headers", [])) > 0
                    and len(section.table_data.get("rows", [])) > 0
                )
                label = "has" if has_data else "is missing"
                checks.append(
                    ValidationCheck(
                        check_name=f"data_table_content_{i}",
                        status=CheckStatus.PASS if has_data else CheckStatus.FAIL,
                        message=f"Data table section {i} {label} content",
                        section_index=i,
                    ),
                )
        return checks

    @staticmethod
    def _check_charts(report: Report) -> list[ValidationCheck]:
        """Verify chart sections have image data."""
        checks: list[ValidationCheck] = []
        for i, section in enumerate(report.sections):
            if section.section_type == SectionType.CHART:
                has_image = (
                    section.media_bytes is not None
                    and len(section.media_bytes) > 0
                )
                label = "has" if has_image else "is missing"
                checks.append(
                    ValidationCheck(
                        check_name=f"chart_image_{i}",
                        status=CheckStatus.PASS if has_image else CheckStatus.WARN,
                        message=f"Chart section {i} {label} image data",
                        section_index=i,
                        severity="warning" if not has_image else "info",
                    ),
                )
        return checks

    @staticmethod
    def _check_titles(report: Report) -> list[ValidationCheck]:
        """Verify titled sections have non-empty titles."""
        checks: list[ValidationCheck] = []
        needs_title = {
            SectionType.TITLE,
            SectionType.HEADING,
            SectionType.DATA_TABLE,
            SectionType.CHART,
        }
        for i, section in enumerate(report.sections):
            if section.section_type in needs_title:
                has_title = bool(section.title or section.content)
                checks.append(
                    ValidationCheck(
                        check_name=f"section_title_{i}",
                        status=CheckStatus.PASS if has_title else CheckStatus.WARN,
                        message=(
                            f"Section {i} ({section.section_type.value}) "
                            f"{'has' if has_title else 'is missing'} a title"
                        ),
                        section_index=i,
                    ),
                )
        return checks
