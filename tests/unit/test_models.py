"""Comprehensive unit tests for pygramattic-reports core data models."""

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from pygramattic_reports.models import (
    ChartFormat,
    ChartRenderer,
    ChartSpec,
    ChartThemeSpec,
    ChartType,
    CheckStatus,
    ColorSpec,
    ColumnSchema,
    ContentType,
    DatabaseSourceConfig,
    Dataset,
    DataType,
    FileSourceConfig,
    FontSpec,
    GoogleSourceConfig,
    Manifest,
    NumberClaim,
    Provenance,
    RawData,
    Report,
    ReportSection,
    SectionSource,
    SectionType,
    SourceConfig,
    SourceType,
    SpacingSpec,
    TemplateSectionSpec,
    TemplateSpec,
    ThemeSpec,
    ValidationCheck,
    ValidationResult,
    generate_id,
    now_utc,
)

# ---- Base Utilities ----


class TestBaseUtilities:
    def test_generate_id_returns_uuid_string(self):
        result = generate_id()
        assert isinstance(result, str)
        assert len(result) == 36

    def test_generate_id_produces_unique_values(self):
        ids = {generate_id() for _ in range(100)}
        assert len(ids) == 100

    def test_now_utc_is_timezone_aware(self):
        ts = now_utc()
        assert ts.tzinfo is not None
        assert ts.tzinfo == UTC

    def test_now_utc_returns_datetime(self):
        ts = now_utc()
        assert hasattr(ts, "year")
        assert hasattr(ts, "microsecond")


# ---- Source Models ----


class TestSourceModels:
    def test_source_type_values(self):
        assert SourceType.CSV.value == "csv"
        assert SourceType.JSON.value == "json"
        assert SourceType.XLSX.value == "xlsx"
        assert SourceType.POSTGRESQL.value == "postgresql"

    def test_file_source_config_defaults(self):
        cfg = FileSourceConfig(path=Path("/tmp/test.csv"))  # noqa: S108
        assert cfg.encoding == "utf-8"
        assert cfg.delimiter == ","
        assert cfg.has_header is True
        assert cfg.sheet_name is None

    def test_file_source_config_custom(self):
        cfg = FileSourceConfig(
            path=Path("/tmp/data.tsv"),  # noqa: S108
            encoding="latin-1",
            delimiter="\t",
            has_header=False,
        )
        assert cfg.encoding == "latin-1"
        assert cfg.delimiter == "\t"
        assert cfg.has_header is False

    def test_file_source_config_frozen(self):
        cfg = FileSourceConfig(path=Path("/tmp/test.csv"))  # noqa: S108
        with pytest.raises(ValidationError):
            cfg.encoding = "latin-1"

    def test_database_source_config_defaults(self):
        cfg = DatabaseSourceConfig(host="localhost", database="mydb")
        assert cfg.port == 5432
        assert cfg.schema_name == "public"
        assert cfg.username is None

    def test_google_source_config(self):
        cfg = GoogleSourceConfig(document_id="abc123")
        assert cfg.document_id == "abc123"
        assert cfg.credentials_path is None

    def test_source_config_with_file(self):
        cfg = SourceConfig(
            source_type=SourceType.CSV,
            name="sales data",
            file=FileSourceConfig(path=Path("/tmp/sales.csv")),  # noqa: S108
        )
        assert cfg.source_type == SourceType.CSV
        assert cfg.name == "sales data"
        assert cfg.file is not None
        assert cfg.database is None

    def test_source_config_frozen(self):
        cfg = SourceConfig(source_type=SourceType.CSV, name="test")
        with pytest.raises(ValidationError):
            cfg.name = "changed"


# ---- RawData ----


class TestRawData:
    def _make_source_config(self):
        return SourceConfig(
            source_type=SourceType.CSV,
            name="test",
            file=FileSourceConfig(path=Path("/tmp/test.csv")),  # noqa: S108
        )

    def test_raw_data_tabular(self):
        raw = RawData(
            id="raw-001",
            source_config=self._make_source_config(),
            content_type=ContentType.TABULAR,
            tabular_data=[{"name": "A", "value": 1}],
            tabular_headers=["name", "value"],
            row_count=1,
            loaded_at=now_utc(),
        )
        assert raw.id == "raw-001"
        assert raw.content_type == ContentType.TABULAR
        assert raw.row_count == 1

    def test_raw_data_document(self):
        raw = RawData(
            id="raw-002",
            source_config=self._make_source_config(),
            content_type=ContentType.DOCUMENT,
            document_text=["Paragraph one.", "Paragraph two."],
            loaded_at=now_utc(),
        )
        assert raw.content_type == ContentType.DOCUMENT
        assert len(raw.document_text) == 2

    def test_raw_data_frozen(self):
        raw = RawData(
            id="raw-003",
            source_config=self._make_source_config(),
            content_type=ContentType.TABULAR,
            loaded_at=now_utc(),
        )
        with pytest.raises(ValidationError):
            raw.id = "changed"

    def test_raw_data_json_roundtrip(self):
        raw = RawData(
            id="raw-rt",
            source_config=self._make_source_config(),
            content_type=ContentType.TABULAR,
            tabular_data=[{"x": 1}],
            loaded_at=now_utc(),
        )
        json_str = raw.model_dump_json()
        restored = RawData.model_validate_json(json_str)
        assert restored.id == raw.id
        assert restored.content_type == raw.content_type


# ---- Dataset ----


class TestDataset:
    def _make_provenance(self):
        return Provenance(
            source_type="csv",
            source_path="/tmp/test.csv",  # noqa: S108
            source_name="test source",
            loaded_at=now_utc(),
            normalized_at=now_utc(),
            row_count_raw=3,
        )

    def test_dataset_creation(self):
        df = pd.DataFrame({"name": ["A", "B", "C"], "value": [1, 2, 3]})
        ds = Dataset(
            id=generate_id(),
            name="test_dataset",
            schema=[
                ColumnSchema(name="name", dtype=DataType.STRING),
                ColumnSchema(name="value", dtype=DataType.INTEGER),
            ],
            dataframe=df,
            provenance=self._make_provenance(),
        )
        assert ds.row_count == 3
        assert ds.column_names == ["name", "value"]
        assert ds.name == "test_dataset"

    def test_dataset_created_at_auto(self):
        df = pd.DataFrame({"x": [1]})
        ds = Dataset(
            id="ds-1",
            name="auto_ts",
            schema=[ColumnSchema(name="x", dtype=DataType.INTEGER)],
            dataframe=df,
            provenance=self._make_provenance(),
        )
        assert ds.created_at.tzinfo == UTC

    def test_dataset_created_at_explicit(self):
        explicit_ts = datetime(2024, 1, 15, tzinfo=UTC)
        df = pd.DataFrame({"x": [1]})
        ds = Dataset(
            id="ds-2",
            name="explicit_ts",
            schema=[ColumnSchema(name="x", dtype=DataType.INTEGER)],
            dataframe=df,
            provenance=self._make_provenance(),
            created_at=explicit_ts,
        )
        assert ds.created_at == explicit_ts

    def test_dataset_to_metadata_dict(self):
        df = pd.DataFrame({"amount": [100.0, 200.0]})
        ds = Dataset(
            id="ds-meta",
            name="revenue",
            schema=[ColumnSchema(name="amount", dtype=DataType.FLOAT)],
            dataframe=df,
            provenance=self._make_provenance(),
        )
        meta = ds.to_metadata_dict()
        assert meta["id"] == "ds-meta"
        assert meta["name"] == "revenue"
        assert meta["row_count"] == 2
        assert len(meta["schema"]) == 1
        assert "provenance" in meta
        assert "created_at" in meta

    def test_dataset_empty_dataframe(self):
        df = pd.DataFrame({"x": pd.Series([], dtype="int64")})
        ds = Dataset(
            id="ds-empty",
            name="empty",
            schema=[ColumnSchema(name="x", dtype=DataType.INTEGER)],
            dataframe=df,
            provenance=self._make_provenance(),
        )
        assert ds.row_count == 0


# ---- ColumnSchema & Provenance ----


class TestColumnSchemaAndProvenance:
    def test_column_schema_creation(self):
        col = ColumnSchema(name="revenue", dtype=DataType.FLOAT, nullable=False)
        assert col.name == "revenue"
        assert col.dtype == DataType.FLOAT
        assert col.nullable is False

    def test_column_schema_defaults(self):
        col = ColumnSchema(name="x", dtype=DataType.STRING)
        assert col.nullable is True
        assert col.description is None

    def test_column_schema_json_roundtrip(self):
        col = ColumnSchema(
            name="score",
            dtype=DataType.FLOAT,
            nullable=False,
            description="Test score",
        )
        json_str = col.model_dump_json()
        restored = ColumnSchema.model_validate_json(json_str)
        assert restored == col

    def test_column_schema_frozen(self):
        col = ColumnSchema(name="x", dtype=DataType.STRING)
        with pytest.raises(ValidationError):
            col.name = "y"

    def test_provenance_creation(self):
        prov = Provenance(
            source_type="xlsx",
            source_path="/data/report.xlsx",
            source_name="quarterly",
            loaded_at=now_utc(),
            normalized_at=now_utc(),
            row_count_raw=500,
            transformations=["drop_nulls", "cast_dates"],
        )
        assert prov.source_type == "xlsx"
        assert len(prov.transformations) == 2

    def test_provenance_default_transformations(self):
        prov = Provenance(
            source_type="csv",
            source_name="test",
            loaded_at=now_utc(),
            normalized_at=now_utc(),
            row_count_raw=10,
        )
        assert prov.transformations == []

    def test_data_type_enum_values(self):
        assert DataType.STRING.value == "string"
        assert DataType.INTEGER.value == "int"
        assert DataType.FLOAT.value == "float"
        assert DataType.BOOLEAN.value == "boolean"


# ---- Report Models ----


class TestReportModels:
    def test_section_type_values(self):
        assert SectionType.TITLE.value == "title"
        assert SectionType.DATA_TABLE.value == "data_table"
        assert SectionType.PAGE_BREAK.value == "page_break"

    def test_report_section_text(self):
        section = ReportSection(
            section_type=SectionType.NARRATIVE,
            title="Summary",
            content="Report content here.",
        )
        assert section.section_type == SectionType.NARRATIVE
        assert section.content == "Report content here."

    def test_report_section_defaults(self):
        section = ReportSection(section_type=SectionType.SPACER)
        assert section.title is None
        assert section.content is None
        assert section.level == 1
        assert section.metadata == {}

    def test_report_section_frozen(self):
        section = ReportSection(section_type=SectionType.TITLE, content="Title")
        with pytest.raises(ValidationError):
            section.content = "Changed"

    def test_number_claim(self):
        claim = NumberClaim(
            section_index=2,
            value=1234.56,
            formatted_value="$1,234.56",
            source_dataset_id="ds-001",
            source_column="revenue",
            computation="sum",
            description="Total revenue",
        )
        assert claim.value == 1234.56
        assert claim.formatted_value == "$1,234.56"

    def test_report_creation(self):
        report = Report(
            id=generate_id(),
            name="Q4 Report",
            sections=[
                ReportSection(section_type=SectionType.TITLE, content="Q4 Report"),
                ReportSection(section_type=SectionType.NARRATIVE, content="Performance summary."),
            ],
            template_name="quarterly",
            theme_name="corporate",
            build_timestamp=now_utc(),
        )
        assert len(report.sections) == 2
        assert report.template_name == "quarterly"
        assert report.number_claims == []
        assert report.build_warnings == []

    def test_report_frozen(self):
        report = Report(
            id="r-1",
            name="test",
            sections=[],
            template_name="default",
            theme_name="default",
            build_timestamp=now_utc(),
        )
        with pytest.raises(ValidationError):
            report.name = "changed"


# ---- ChartSpec ----


class TestChartSpec:
    def test_chart_spec_defaults(self):
        spec = ChartSpec(
            chart_type=ChartType.BAR,
            title="Revenue by Region",
            x_column="region",
            y_columns=["revenue"],
            dataset_id="ds-001",
        )
        assert spec.width == 800
        assert spec.height == 600
        assert spec.dpi == 150
        assert spec.renderer == ChartRenderer.MATPLOTLIB
        assert spec.output_format == ChartFormat.PNG
        assert spec.legend is True

    def test_chart_spec_custom(self):
        spec = ChartSpec(
            chart_type=ChartType.LINE,
            title="Trend",
            x_column="date",
            y_columns=["revenue", "cost"],
            dataset_id="ds-002",
            width=1200,
            height=800,
            renderer=ChartRenderer.MATPLOTLIB,
            output_format=ChartFormat.SVG,
            legend_position="upper left",
        )
        assert spec.chart_type == ChartType.LINE
        assert len(spec.y_columns) == 2
        assert spec.width == 1200

    def test_chart_type_enum(self):
        assert ChartType.BAR.value == "bar"
        assert ChartType.PIE.value == "pie"
        assert ChartType.HEATMAP.value == "heatmap"

    def test_chart_spec_frozen(self):
        spec = ChartSpec(
            chart_type=ChartType.BAR,
            title="Test",
            x_column="x",
            y_columns=["y"],
            dataset_id="id",
        )
        with pytest.raises(ValidationError):
            spec.title = "Changed"


# ---- Template & Theme ----


class TestTemplateAndTheme:
    def test_section_source_values(self):
        assert SectionSource.STATIC.value == "static"
        assert SectionSource.AI_GENERATED.value == "ai_generated"

    def test_template_section_spec(self):
        sec = TemplateSectionSpec(type="title", content="Q4 Report")
        assert sec.type == "title"
        assert sec.source == SectionSource.STATIC

    def test_template_spec_creation(self):
        template = TemplateSpec(
            name="quarterly",
            sections=[
                TemplateSectionSpec(type="title", content="Q4 Report"),
                TemplateSectionSpec(
                    type="narrative",
                    source=SectionSource.AI_GENERATED,
                    ai_prompt="Summarize the data",
                ),
            ],
        )
        assert len(template.sections) == 2
        assert template.version == "1.0"

    def test_font_spec_defaults(self):
        fonts = FontSpec()
        assert fonts.heading == "Arial"
        assert fonts.body == "Calibri"
        assert fonts.size_body == 11

    def test_color_spec_defaults(self):
        colors = ColorSpec()
        assert colors.primary == "#1a5276"
        assert len(colors.chart_palette) == 8

    def test_spacing_spec_defaults(self):
        spacing = SpacingSpec()
        assert spacing.section_gap_pt == 18
        assert spacing.page_margin_inches == 1.0

    def test_chart_theme_spec_defaults(self):
        chart_theme = ChartThemeSpec()
        assert chart_theme.grid is True
        assert chart_theme.grid_alpha == 0.5

    def test_theme_spec_defaults(self):
        theme = ThemeSpec(name="default")
        assert theme.fonts.body == "Calibri"
        assert theme.colors.primary == "#1a5276"
        assert theme.spacing.page_margin_inches == 1.0
        assert theme.chart.grid is True

    def test_theme_spec_custom(self):
        theme = ThemeSpec(
            name="dark",
            description="Dark theme",
            colors=ColorSpec(
                primary="#ffffff",
                background="#1a1a1a",
                text="#e0e0e0",
            ),
        )
        assert theme.colors.primary == "#ffffff"
        assert theme.colors.background == "#1a1a1a"

    def test_template_spec_frozen(self):
        template = TemplateSpec(
            name="test",
            sections=[TemplateSectionSpec(type="title")],
        )
        with pytest.raises(ValidationError):
            template.name = "changed"


# ---- Validation ----


class TestValidation:
    def test_check_status_values(self):
        assert CheckStatus.PASS.value == "pass"
        assert CheckStatus.FAIL.value == "fail"
        assert CheckStatus.WARN.value == "warn"
        assert CheckStatus.SKIP.value == "skip"

    def test_validation_check(self):
        check = ValidationCheck(
            check_name="row_count",
            status=CheckStatus.PASS,
            message="Row count matches",
            expected="100",
            actual="100",
        )
        assert check.status == CheckStatus.PASS
        assert check.severity == "error"

    def test_validation_result(self):
        result = ValidationResult(
            report_id="r-123",
            overall_status=CheckStatus.PASS,
            checks=[
                ValidationCheck(
                    check_name="row_count",
                    status=CheckStatus.PASS,
                    message="Row count matches",
                ),
                ValidationCheck(
                    check_name="format_check",
                    status=CheckStatus.WARN,
                    message="Minor formatting issue",
                    severity="warning",
                ),
            ],
            total_checks=2,
            passed=1,
            failed=0,
            warnings=1,
            validated_at=now_utc(),
        )
        assert result.overall_status == CheckStatus.PASS
        assert result.total_checks == 2
        assert len(result.checks) == 2

    def test_validation_result_frozen(self):
        result = ValidationResult(
            report_id="r-1",
            overall_status=CheckStatus.PASS,
            checks=[],
            total_checks=0,
            passed=0,
            failed=0,
            warnings=0,
            validated_at=now_utc(),
        )
        with pytest.raises(ValidationError):
            result.report_id = "changed"


# ---- Manifest ----


class TestManifest:
    def test_manifest_creation(self):
        manifest = Manifest(
            id="ds-123",
            name="revenue",
            source_type="csv",
            source_path="/data/revenue.csv",
            columns=[ColumnSchema(name="amount", dtype=DataType.FLOAT)],
            row_count=100,
            created_at=now_utc(),
            storage_path="processed/revenue/data.parquet",
        )
        assert manifest.row_count == 100
        assert manifest.format == "parquet"
        assert manifest.tags == []

    def test_manifest_with_tags(self):
        manifest = Manifest(
            id="ds-456",
            name="expenses",
            source_type="xlsx",
            columns=[ColumnSchema(name="cost", dtype=DataType.FLOAT)],
            row_count=50,
            created_at=now_utc(),
            storage_path="processed/expenses/data.parquet",
            tags=["finance", "quarterly"],
            size_bytes=4096,
        )
        assert len(manifest.tags) == 2
        assert manifest.size_bytes == 4096

    def test_manifest_json_roundtrip(self):
        manifest = Manifest(
            id="ds-rt",
            name="test",
            source_type="csv",
            columns=[ColumnSchema(name="x", dtype=DataType.INTEGER)],
            row_count=10,
            created_at=now_utc(),
            storage_path="processed/test/data.parquet",
        )
        json_str = manifest.model_dump_json()
        restored = Manifest.model_validate_json(json_str)
        assert restored == manifest

    def test_manifest_frozen(self):
        manifest = Manifest(
            id="ds-f",
            name="frozen",
            source_type="csv",
            columns=[],
            row_count=0,
            created_at=now_utc(),
            storage_path="x",
        )
        with pytest.raises(ValidationError):
            manifest.name = "changed"


# ---- Rejection Tests ----


class TestRejection:
    def test_column_schema_rejects_invalid_dtype(self):
        with pytest.raises(ValidationError):
            ColumnSchema(name="x", dtype="not_a_type")

    def test_chart_spec_rejects_invalid_chart_type(self):
        with pytest.raises(ValidationError):
            ChartSpec(
                chart_type="invalid",
                title="Bad",
                x_column="x",
                y_columns=["y"],
                dataset_id="id",
            )

    def test_source_config_rejects_invalid_source_type(self):
        with pytest.raises(ValidationError):
            SourceConfig(source_type="invalid", name="test")

    def test_validation_check_rejects_invalid_status(self):
        with pytest.raises(ValidationError):
            ValidationCheck(
                check_name="test",
                status="invalid",
                message="bad",
            )
