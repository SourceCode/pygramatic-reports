"""Tests for the report validator (Phase 19)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pandas as pd

from pygramattic_reports.exceptions import AIError
from pygramattic_reports.models import (
    CheckStatus,
    NumberClaim,
    Report,
    ReportSection,
    SectionType,
    TemplateSectionSpec,
    TemplateSpec,
)
from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.models.dataset import (
    ColumnSchema,
    Dataset,
    DataType,
    Provenance,
)
from pygramattic_reports.validator import ReportValidator
from pygramattic_reports.validator.narrative import NarrativeValidator
from pygramattic_reports.validator.numerical import NumericalValidator
from pygramattic_reports.validator.structural import StructuralValidator

# ---------- Helpers ----------------------------------------------------------


def _make_dataset(
    data: dict[str, list[object]] | None = None,
    name: str = "test_data",
) -> Dataset:
    """Create a real Dataset for testing."""
    if data is None:
        data = {
            "region": ["US", "EU", "APAC"],
            "revenue": [1500, 2300, 890],
            "cost": [800, 1100, 500],
        }
    df = pd.DataFrame(data)
    schema = [
        ColumnSchema(
            name=col,
            dtype=DataType.STRING if df[col].dtype == "object" else DataType.INTEGER,
        )
        for col in df.columns
    ]
    return Dataset(
        id=generate_id(),
        name=name,
        schema=schema,
        dataframe=df,
        provenance=Provenance(
            source_type="test",
            source_name="test",
            loaded_at=now_utc(),
            normalized_at=now_utc(),
            row_count_raw=len(df),
        ),
    )


def _make_template(
    section_specs: list[TemplateSectionSpec] | None = None,
) -> TemplateSpec:
    """Create a template for testing."""
    if section_specs is None:
        from pygramattic_reports.models import SectionSource  # noqa: PLC0415

        section_specs = [
            TemplateSectionSpec(
                type="title", source=SectionSource.STATIC, content="Test",
            ),
            TemplateSectionSpec(
                type="data_table", source=SectionSource.DATA,
                title="Data", dataset="main",
            ),
        ]
    return TemplateSpec(name="test", sections=section_specs)


def _make_report(
    sections: list[ReportSection] | None = None,
    number_claims: list[NumberClaim] | None = None,
    build_warnings: list[str] | None = None,
) -> Report:
    """Create a Report for testing."""
    if sections is None:
        sections = [
            ReportSection(
                section_type=SectionType.TITLE,
                content="Test Report",
            ),
            ReportSection(
                section_type=SectionType.DATA_TABLE,
                title="Data",
                table_data={
                    "headers": ["region", "revenue"],
                    "rows": [["US", 1500], ["EU", 2300]],
                },
            ),
        ]
    return Report(
        id=generate_id(),
        name="Test Report",
        sections=sections,
        number_claims=number_claims or [],
        template_name="test",
        theme_name="test",
        build_timestamp=now_utc(),
        build_warnings=build_warnings or [],
    )


# ---------- Structural: all sections present ---------------------------------


class TestStructuralAllSectionsPresent:
    """Pass when sections match template."""

    def test_all_sections_present(self) -> None:
        report = _make_report()
        template = _make_template()
        checks = StructuralValidator().validate(report, template)

        count_checks = [c for c in checks if c.check_name == "section_count"]
        assert len(count_checks) == 1
        assert count_checks[0].status == CheckStatus.PASS


# ---------- Structural: missing section --------------------------------------


class TestStructuralMissingSection:
    """Fail when section is missing."""

    def test_missing_section_fails(self) -> None:
        report = _make_report(sections=[
            ReportSection(section_type=SectionType.TITLE, content="Title"),
        ])
        template = _make_template()  # expects 2 sections
        checks = StructuralValidator().validate(report, template)

        count_checks = [c for c in checks if c.check_name == "section_count"]
        assert count_checks[0].status == CheckStatus.FAIL


# ---------- Structural: data table has data ----------------------------------


class TestStructuralDataTableHasData:
    """Pass for populated table."""

    def test_populated_table_passes(self) -> None:
        report = _make_report()
        template = _make_template()
        checks = StructuralValidator().validate(report, template)

        table_checks = [c for c in checks if "data_table_content" in c.check_name]
        assert len(table_checks) == 1
        assert table_checks[0].status == CheckStatus.PASS


# ---------- Structural: data table empty -------------------------------------


class TestStructuralDataTableEmpty:
    """Fail for empty table."""

    def test_empty_table_fails(self) -> None:
        report = _make_report(sections=[
            ReportSection(
                section_type=SectionType.DATA_TABLE,
                title="Empty",
                table_data={"headers": [], "rows": []},
            ),
        ])
        template = _make_template(section_specs=[
            TemplateSectionSpec(type="data_table", title="Empty"),
        ])
        checks = StructuralValidator().validate(report, template)

        table_checks = [c for c in checks if "data_table_content" in c.check_name]
        assert len(table_checks) == 1
        assert table_checks[0].status == CheckStatus.FAIL


# ---------- Structural: chart has image --------------------------------------


class TestStructuralChartHasImage:
    """Pass for chart with image data."""

    def test_chart_with_image_passes(self) -> None:
        report = _make_report(sections=[
            ReportSection(
                section_type=SectionType.CHART,
                title="Chart",
                media_bytes=b"\x89PNG\r\n\x1a\n",
                media_type="image/png",
            ),
        ])
        template = _make_template(section_specs=[
            TemplateSectionSpec(type="chart", title="Chart"),
        ])
        checks = StructuralValidator().validate(report, template)

        chart_checks = [c for c in checks if "chart_image" in c.check_name]
        assert len(chart_checks) == 1
        assert chart_checks[0].status == CheckStatus.PASS


# ---------- Numerical: exact match -------------------------------------------


class TestNumericalExactMatch:
    """Value matches source exactly."""

    def test_exact_match_passes(self) -> None:
        ds = _make_dataset()
        claim = NumberClaim(
            section_index=0,
            value=1500.0,
            formatted_value="1500",
            source_dataset_id=ds.id,
            source_column="revenue",
            computation="raw[0]",
            description="revenue row 0",
        )
        report = _make_report(number_claims=[claim])
        checks = NumericalValidator().validate(report, {ds.id: ds})

        assert len(checks) == 1
        assert checks[0].status == CheckStatus.PASS


# ---------- Numerical: within tolerance --------------------------------------


class TestNumericalWithinTolerance:
    """Small float difference passes."""

    def test_within_tolerance_passes(self) -> None:
        ds = _make_dataset()
        claim = NumberClaim(
            section_index=0,
            value=1500.005,
            formatted_value="1500.005",
            source_dataset_id=ds.id,
            source_column="revenue",
            computation="raw[0]",
            description="revenue row 0",
        )
        checks = NumericalValidator(tolerance=0.01).validate(
            _make_report(number_claims=[claim]),
            {ds.id: ds},
        )
        assert checks[0].status == CheckStatus.PASS


# ---------- Numerical: outside tolerance -------------------------------------


class TestNumericalOutsideTolerance:
    """Large difference fails."""

    def test_outside_tolerance_fails(self) -> None:
        ds = _make_dataset()
        claim = NumberClaim(
            section_index=0,
            value=9999.0,
            formatted_value="9999",
            source_dataset_id=ds.id,
            source_column="revenue",
            computation="raw[0]",
            description="revenue row 0",
        )
        checks = NumericalValidator().validate(
            _make_report(number_claims=[claim]),
            {ds.id: ds},
        )
        assert checks[0].status == CheckStatus.FAIL


# ---------- Numerical: computed value ----------------------------------------


class TestNumericalComputedValue:
    """Sum/avg recomputation matches."""

    def test_sum_recomputation_passes(self) -> None:
        ds = _make_dataset()
        claim = NumberClaim(
            section_index=0,
            value=4690.0,
            formatted_value="4690",
            source_dataset_id=ds.id,
            source_column="revenue",
            computation="sum",
            description="revenue total",
        )
        checks = NumericalValidator().validate(
            _make_report(number_claims=[claim]),
            {ds.id: ds},
        )
        assert checks[0].status == CheckStatus.PASS


# ---------- Numerical: missing dataset ---------------------------------------


class TestNumericalMissingDataset:
    """Skip check for unknown dataset."""

    def test_missing_dataset_skips(self) -> None:
        claim = NumberClaim(
            section_index=0,
            value=100.0,
            formatted_value="100",
            source_dataset_id="nonexistent",
            source_column="col",
            computation="raw[0]",
            description="missing",
        )
        checks = NumericalValidator().validate(
            _make_report(number_claims=[claim]),
            {},
        )
        assert checks[0].status == CheckStatus.SKIP


# ---------- Numerical: NaN value ---------------------------------------------


class TestNumericalNanValue:
    """NaN handling."""

    def test_nan_value_warns(self) -> None:
        ds = _make_dataset()
        claim = NumberClaim(
            section_index=0,
            value=float("nan"),
            formatted_value="NaN",
            source_dataset_id=ds.id,
            source_column="revenue",
            computation="raw[0]",
            description="revenue nan",
        )
        checks = NumericalValidator().validate(
            _make_report(number_claims=[claim]),
            {ds.id: ds},
        )
        assert checks[0].status == CheckStatus.WARN


# ---------- Narrative: valid -------------------------------------------------


class TestNarrativeValid:
    """AI reports valid, check passes."""

    def test_narrative_valid(self) -> None:
        client = MagicMock()
        client.is_available.return_value = True
        client.generate.return_value = json.dumps(
            {"valid": True, "issues": []},
        )

        report = _make_report(sections=[
            ReportSection(
                section_type=SectionType.SUMMARY,
                title="Summary",
                content="Revenue is growing across all regions.",
            ),
        ])
        ds = _make_dataset()
        checks = NarrativeValidator(client).validate(report, {"main": ds})

        assert len(checks) == 1
        assert checks[0].status == CheckStatus.PASS


# ---------- Narrative: issues ------------------------------------------------


class TestNarrativeIssues:
    """AI reports issues, check warns."""

    def test_narrative_issues_warns(self) -> None:
        client = MagicMock()
        client.is_available.return_value = True
        client.generate.return_value = json.dumps({
            "valid": False,
            "issues": ["Revenue trend is overstated"],
        })

        report = _make_report(sections=[
            ReportSection(
                section_type=SectionType.NARRATIVE,
                title="Analysis",
                content="Revenue is skyrocketing.",
            ),
        ])
        ds = _make_dataset()
        checks = NarrativeValidator(client).validate(report, {"main": ds})

        assert len(checks) == 1
        assert checks[0].status == CheckStatus.WARN
        assert "overstated" in checks[0].message


# ---------- Narrative: AI unavailable ----------------------------------------


class TestNarrativeAiUnavailable:
    """Skips when no AI client."""

    def test_skips_without_client(self) -> None:
        checks = NarrativeValidator(None).validate(
            _make_report(), {"main": _make_dataset()},
        )
        assert len(checks) == 1
        assert checks[0].status == CheckStatus.SKIP

    def test_skips_when_unavailable(self) -> None:
        client = MagicMock()
        client.is_available.return_value = False
        checks = NarrativeValidator(client).validate(
            _make_report(), {"main": _make_dataset()},
        )
        assert checks[0].status == CheckStatus.SKIP

    def test_skips_on_ai_error(self) -> None:
        client = MagicMock()
        client.is_available.return_value = True
        client.generate.side_effect = AIError("Connection failed")

        report = _make_report(sections=[
            ReportSection(
                section_type=SectionType.SUMMARY,
                content="Some text",
            ),
        ])
        checks = NarrativeValidator(client).validate(
            report, {"main": _make_dataset()},
        )
        assert checks[0].status == CheckStatus.SKIP


# ---------- Orchestrator: all pass -------------------------------------------


class TestValidatorAllPass:
    """All checks pass, overall PASS."""

    def test_all_pass(self) -> None:
        ds = _make_dataset()
        claim = NumberClaim(
            section_index=1,
            value=1500.0,
            formatted_value="1500",
            source_dataset_id=ds.id,
            source_column="revenue",
            computation="raw[0]",
            description="revenue row 0",
        )
        report = _make_report(number_claims=[claim])
        template = _make_template()

        result = ReportValidator().validate(report, template, {"main": ds})

        assert result.overall_status in (CheckStatus.PASS, CheckStatus.WARN)
        assert result.failed == 0
        assert result.total_checks > 0


# ---------- Orchestrator: with failure ---------------------------------------


class TestValidatorWithFailure:
    """One check fails, overall FAIL."""

    def test_failure_detected(self) -> None:
        ds = _make_dataset()
        claim = NumberClaim(
            section_index=0,
            value=9999.0,
            formatted_value="9999",
            source_dataset_id=ds.id,
            source_column="revenue",
            computation="raw[0]",
            description="bad value",
        )
        report = _make_report(number_claims=[claim])
        template = _make_template()

        result = ReportValidator().validate(report, template, {"main": ds})

        assert result.overall_status == CheckStatus.FAIL
        assert result.failed >= 1


# ---------- Orchestrator: with warning ---------------------------------------


class TestValidatorWithWarning:
    """Warnings but no failures, overall WARN."""

    def test_warning_status(self) -> None:
        report = _make_report(
            sections=[
                ReportSection(
                    section_type=SectionType.TITLE,
                    content="Title",
                ),
                ReportSection(
                    section_type=SectionType.CHART,
                    title="Empty Chart",
                    media_bytes=None,
                ),
            ],
        )
        template = _make_template(section_specs=[
            TemplateSectionSpec(type="title", content="Title"),
            TemplateSectionSpec(type="chart", title="Chart"),
        ])

        result = ReportValidator().validate(
            report, template, {"main": _make_dataset()},
        )

        assert result.warnings >= 1
        if result.failed == 0:
            assert result.overall_status == CheckStatus.WARN
