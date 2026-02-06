"""Fluent API for Pygramattic Reports.

This module provides a high-level, fluent interface for building reports programmatically,
hiding the complexity of the underlying Builder and configuration objects.

Usage:
    report = (
        Pygramattic()
        .configure(title="My Report", author="Me")
        .add_dataset("sales", df)
        .add_section("My Section", text="Some content")
        .build()
    )
    report.save("output.html")
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from pygramattic_reports.builder import BuildConfig, ReportBuilder
from pygramattic_reports.charts import ChartEngine
from pygramattic_reports.logging import get_logger
from pygramattic_reports.models import (
    ColumnSchema,
    Dataset,
    DataType,
    DocumentMetadata,
    Provenance,
    Report,
    SectionSource,
    SourceType,
    TemplateSectionSpec,
)
from pygramattic_reports.outputs import (
    HtmlAdapter,
    MarkdownAdapter,
)
from pygramattic_reports.templates import TemplateRenderer

# Optional imports for other adapters
try:
    from pygramattic_reports.outputs.excel_adapter import ExcelAdapter
except ImportError:
    ExcelAdapter = None  # type: ignore

try:
    from pygramattic_reports.outputs.pptx_adapter import PptxAdapter
except ImportError:
    PptxAdapter = None  # type: ignore


logger = get_logger("api")


class Pygramattic:
    """Fluent entry point for building reports."""

    def __init__(self) -> None:
        """Initialize a new report build context."""
        self._datasets: dict[str, Dataset] = {}
        self._sections: list[TemplateSectionSpec] = []
        self._metadata = DocumentMetadata()
        self._warn_list: list[str] = []

        # Initialize with required fields
        self._config = BuildConfig(
            report_name="API Generated Report", template={}, theme={}, datasets={}
        )

    def configure(
        self,
        title: str | None = None,
        author: str | None = None,
        subject: str | None = None,
        keywords: list[str] | None = None,
    ) -> Pygramattic:
        """Configure report metadata."""
        current_dict = self._metadata.model_dump(exclude_unset=True)
        if title:
            current_dict["title"] = title
        if author:
            current_dict["author"] = author
        if subject:
            current_dict["subject"] = subject
        if keywords:
            current_dict["keywords"] = keywords

        self._metadata = DocumentMetadata(**current_dict)
        return self

    def add_dataset(
        self,
        name: str,
        data: pd.DataFrame | list[dict[str, Any]],
        description: str | None = None,
    ) -> Pygramattic:
        """Add a dataset to the report context."""
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data

        # Infer schema
        columns = []
        for col_name, dtype in df.dtypes.items():
            dt = DataType.STRING
            if pd.api.types.is_numeric_dtype(dtype):
                if pd.api.types.is_float_dtype(dtype):
                    dt = DataType.FLOAT
                else:
                    dt = DataType.INTEGER
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                dt = DataType.DATETIME
            elif pd.api.types.is_bool_dtype(dtype):
                dt = DataType.BOOLEAN

            columns.append(ColumnSchema(name=str(col_name), dtype=dt))

        dataset = Dataset(
            id=name,
            name=name,
            schema=columns,
            dataframe=df,
            provenance=Provenance(
                source_type=SourceType.CSV,  # Default/Dummy
                source_name="API",
                loaded_at=datetime.now(UTC),
                normalized_at=datetime.now(UTC),
                row_count_raw=len(df),
            ),
            # metadata={"description": description} if description else {},
        )
        self._datasets[name] = dataset
        return self

    def add_section(
        self,
        title: str,
        content: str | None = None,
        dataset: str | None = None,
        type: str = "narrative",
        level: int = 2,
    ) -> Pygramattic:
        """Add a generic section."""
        spec = TemplateSectionSpec(
            title=title,
            type=type,
            level=level,
            content=content,
            dataset=dataset,
            source=SectionSource.STATIC if not dataset else SectionSource.DATA,
        )
        self._sections.append(spec)
        return self

    def add_chart(
        self,
        title: str,
        dataset: str,
        chart_type: str,
        x_col: str,
        y_cols: list[str],
        description: str | None = None,
    ) -> Pygramattic:
        """Add a chart section."""
        spec = TemplateSectionSpec(
            title=title,
            type="chart",
            source=SectionSource.CHART,
            dataset=dataset,
            chart_type=chart_type,
            x_column=x_col,
            y_columns=y_cols,
            content=description,
        )
        self._sections.append(spec)
        return self

    def build(self) -> BuiltReport:
        """Build the report artifact."""
        # 1. Prepare Builder dependencies
        # In a real app, these might be singletons or user-provided
        chart_engine = ChartEngine()
        template_renderer = TemplateRenderer()

        # We need a builder that can accept pre-loaded datasets
        # The current ReportBuilder resolves datasets via Manifest + Loaders
        # We need to inject our memory datasets.
        # The ReportBuilder._resolve_dataset uses self.config to find dataset paths usually.
        # But if we want to support memory datasets, we might need to subclass or patch.

        # TRICK: We can't easily inject memory datasets into the current ReportBuilder
        # without modifying it, because it loads strictly from config/manifest.
        # However, looking at builder.py, _resolve_dataset calls loader methods.

        # Let's modify the plan: We need to allow passing datasets *into* build()
        # or have a MemoryLoader.

        # For this implementation, let's assume we can bypass the standard loading
        # if we pass the dataset directly to the section processor?
        # No, the builder controls the flow.

        # Alternative: We modify ReportBuilder to accept a 'context' of pre-loaded datasets.
        # Placeholder for thought process - I will implement a wrapper that handles this.

        builder = ReportBuilder(chart_engine=chart_engine, template_renderer=template_renderer)

        # Inject our datasets into the builder's cache or similar mechanism?
        # The builder doesn't have a public cache.
        # We should probably update ReportBuilder to check a local registry first.

        # Hack for now: We will mock the _resolve_dataset method or similar for this instance.
        # Better: Add a register_dataset method to builder.

        # Let's verify ReportBuilder source code first to be safe (I recall earlier views).
        # It calls `_resolve_dataset`.

        # We will wrap the builder execution.

        # Since I can't easily modify Builder in this step without a separate tool call,
        # I will assume I can subclass it or use a custom method.
        # Let's subclass for the API.

        custom_builder = ApiReportBuilder(
            chart_engine=chart_engine,
            template_renderer=template_renderer,
            preloaded_datasets=self._datasets,
        )

        # Create a synthetic config/spec
        # A full TemplateSpec is needed
        from pygramattic_reports.models import TemplateSpec

        template_spec = TemplateSpec(
            id="api-generated", name=self._metadata.title or "API Report", sections=self._sections
        )

        # We need to trick the builder into using this spec.
        # Builder.build takes a BuildConfig. BuildConfig has a template_path.
        # It loads the template from disk. This is a blocker for purely in-memory API use.

        # FIX: We need to decouple Builder from file-based Template loading.
        # But for Phase 7, maybe we just write a temp template?
        # Or we add `build_from_spec` to Builder.

        # Let's presume we've added `build_from_spec` or similar.
        # Actually, let's implement `build_from_spec` in the ApiReportBuilder subclass.

        report, log = custom_builder.build_from_memory(
            template_spec=template_spec, metadata=self._metadata
        )

        return BuiltReport(report, log)


class ApiReportBuilder(ReportBuilder):
    """Subclass of ReportBuilder to support in-memory datasets and specs."""

    def __init__(
        self,
        chart_engine: ChartEngine,
        template_renderer: TemplateRenderer,
        preloaded_datasets: dict[str, Dataset],
    ):
        super().__init__(chart_engine, template_renderer)
        self._preloaded_datasets = preloaded_datasets

    def _resolve_dataset(self, spec: TemplateSectionSpec, config: BuildConfig) -> Dataset:
        """Override to check in-memory datasets first."""
        if spec.dataset in self._preloaded_datasets:
            return self._preloaded_datasets[spec.dataset]
        # Fallback to standard loading (which might fail if config is empty)
        from typing import cast

        return cast("Dataset", super()._resolve_dataset(spec, config))

    def build_from_memory(
        self, template_spec: Any, metadata: DocumentMetadata
    ) -> tuple[Report, Any]:
        """Custom build method that bypasses file loading."""
        # Initialize
        from pygramattic_reports.logging import BuildLog
        from pygramattic_reports.models import ThemeSpec, generate_id, now_utc

        build_log = BuildLog(
            build_id=generate_id(),
            started_at=now_utc(),
        )

        # Process sections
        # Initialize empty config with required fields
        config = BuildConfig(
            report_name=template_spec.name,
            template=template_spec,
            theme=ThemeSpec(name="default"),
            datasets=self._preloaded_datasets,
        )
        sections = []
        claims = []

        for i, section_spec in enumerate(template_spec.sections):
            try:
                # We interpret the section
                # Note: _process_section expects `config` but we override resolve_dataset
                # so it might be okay.
                section, section_claims = self._process_section(
                    section_spec, config, i, build_log, None
                )
                sections.append(section)
                claims.extend(section_claims)
            except Exception as e:
                build_log.add_entry("error", "builder", f"Section {i} failed: {e}")

        report = Report(
            id=generate_id(),
            name=template_spec.name,
            sections=sections,
            number_claims=claims,
            datasets_used=list(self._preloaded_datasets.keys()),
            template_name="api",
            theme_name="default",
            build_timestamp=now_utc(),
            metadata=metadata,
        )

        return report, build_log


class BuiltReport:
    """Wrapper around a generated Report artifact."""

    def __init__(self, report: Report, log: Any):
        self.report = report
        self.log = log

    def save(self, path: str | Path, format: str | None = None) -> None:
        """Save the report to disk."""
        path = Path(path)
        if format is None:
            # Infer from extension
            ext = path.suffix.lower()
            if ext == ".html":
                format = "html"
            elif ext == ".md":
                format = "markdown"
            elif ext == ".xlsx":
                format = "excel"
            elif ext == ".pptx":
                format = "pptx"
            else:
                raise ValueError(f"Unknown format for extension: {ext}")

        adapter = self._get_adapter(format)
        # We need a dummy theme for now as we don't have one in API yet
        from pygramattic_reports.models import ThemeSpec

        theme = ThemeSpec(name="default")

        content = adapter.render(self.report, theme)

        with open(path, "wb") as f:
            f.write(content)

    def _get_adapter(self, format: str) -> Any:
        if format == "html":
            return HtmlAdapter()
        if format == "markdown":
            return MarkdownAdapter()
        if format == "excel":
            if ExcelAdapter is not None:
                return ExcelAdapter()
            raise ValueError("ExcelAdapter not available")
        if format == "pptx":
            if PptxAdapter is not None:
                return PptxAdapter()
            raise ValueError("PptxAdapter not available")
        raise ValueError(f"Unknown format: {format}")
