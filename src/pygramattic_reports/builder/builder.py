"""Core report builder for pygramattic-reports.

Assembles reports from templates, themes, and datasets by
orchestrating section processors and the chart engine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pygramattic_reports.exceptions import BuildError, ErrorSeverity, PygramatticError
from pygramattic_reports.logging import BuildLog, get_logger
from pygramattic_reports.models import (
    CoverPageSpec,
    DocumentMetadata,
    PageLayout,
    Report,
    ReportSection,
    RunningElement,
    SectionSource,
    SectionType,
    generate_id,
    now_utc,
)
from pygramattic_reports.processors.data_processor import DataProcessor

from .section_processors import (
    process_ai_placeholder_section,
    process_chart_section,
    process_data_table_section,
    process_static_section,
)

if TYPE_CHECKING:
    from pygramattic_reports.ai import ClaudeClient
    from pygramattic_reports.charts import ChartEngine
    from pygramattic_reports.models import (
        Dataset,
        NumberClaim,
        TemplateSectionSpec,
    )
    from pygramattic_reports.processors.data_processor import DataProcessor
    from pygramattic_reports.templates import TemplateRenderer

    from .ai_processor import AISectionProcessor
    from .config import BuildConfig

_logger = get_logger("builder")


class ReportBuilder:
    """Core report assembly engine.

    Takes a report configuration and assembles a Report by:

    1. Loading and resolving the template
    2. Loading the theme
    3. For each section in the template:

       a. STATIC: render the content directly
       b. DATA: build a data table from the referenced dataset
       c. CHART: generate a chart using the chart engine
       d. AI_GENERATED: invoke Claude CLI (or fallback)

    4. Collect all sections into a Report object
    5. Track number claims for validation
    """

    def __init__(
        self,
        chart_engine: ChartEngine,
        template_renderer: TemplateRenderer,
        claude_client: ClaudeClient | None = None,
    ) -> None:
        """Initialize with chart engine, template renderer, and optional AI client."""
        self.chart_engine = chart_engine
        self.template_renderer = template_renderer
        self.claude_client = claude_client
        self.data_processor = DataProcessor()

    def build(
        self,
        config: BuildConfig,
    ) -> tuple[Report, BuildLog]:
        """Build a report from the given configuration.

        Args:
            config: Report build configuration specifying template,
                theme, datasets, and output preferences.

        Returns:
            Tuple of (Report, BuildLog).

        Raises:
            BuildError: If the build fails fatally.
        """
        build_log = BuildLog(
            build_id=generate_id(),
            started_at=now_utc(),
        )

        ai_processor = self._create_ai_processor(config)

        context = self._build_context(config)
        resolved_sections = self.template_renderer.resolve_template(
            config.template,
            context,
        )

        report_sections: list[ReportSection] = []
        number_claims: list[NumberClaim] = []

        # --- Phase 2: Metadata & Structure Extraction ---
        metadata_dict = config.template.metadata or {}
        # Merge build config version if not present
        if "version" not in metadata_dict:
            metadata_dict["version"] = config.template.version

        doc_metadata = DocumentMetadata(
            title=metadata_dict.get("title", config.report_name),
            author=metadata_dict.get("author"),
            subject=metadata_dict.get("subject"),
            keywords=metadata_dict.get("keywords", []),
            version=metadata_dict.get("version"),
            created_at=now_utc(),
        )

        # Extract layout configs
        page_layout = PageLayout(**(config.template.page_layout or {}))
        cover_page = None
        if config.template.cover_page:
            cover_page = CoverPageSpec(**config.template.cover_page)
            # Inject Cover Page Section
            report_sections.append(
                ReportSection(
                    section_type=SectionType.COVER_PAGE,
                    title="Cover Page",
                    metadata={"spec": cover_page.model_dump()},
                )
            )

        header = RunningElement(**config.template.header) if config.template.header else None
        footer = RunningElement(**config.template.footer) if config.template.footer else None

        # --- Section Processing ---

        for i, section_spec in enumerate(resolved_sections):
            try:
                section, claims = self._process_section(
                    section_spec,
                    config,
                    i,
                    build_log,
                    ai_processor,
                )
                report_sections.append(section)
                number_claims.extend(claims)
                build_log.sections_generated += 1
            except Exception as exc:
                if self._is_recoverable(exc):
                    _logger.warning(
                        "Section skipped",
                        index=i,
                        error=str(exc),
                    )
                    build_log.add_entry(
                        "warning",
                        "builder",
                        f"Section {i} skipped: {exc}",
                    )
                    build_log.sections_skipped += 1
                else:
                    build_log.finalize("failed")
                    raise

        status = "completed" if build_log.sections_skipped == 0 else "completed_with_warnings"
        build_log.finalize(status)

        report = Report(
            id=generate_id(),
            name=config.report_name,
            sections=report_sections,
            number_claims=number_claims,
            datasets_used=[ds.id for ds in config.datasets.values()],
            template_name=config.template.name,
            theme_name=config.theme.name,
            build_timestamp=now_utc(),
            build_warnings=[e.message for e in build_log.entries if e.level == "warning"],
            # Phase 2 Fields
            metadata=doc_metadata,
            page_layout=page_layout,
            cover_page=cover_page,
            header=header,
            footer=footer,
        )

        return report, build_log

    # -- internal helpers ------------------------------------------------------

    @staticmethod
    def _build_context(config: BuildConfig) -> dict[str, Any]:
        """Build the Jinja2 template context from config."""
        context: dict[str, Any] = {
            "report_title": config.report_name,
        }
        if config.primary_dataset:
            context["primary_dataset"] = config.primary_dataset
            ds = config.datasets.get(config.primary_dataset)
            if ds:
                context["dataset_name"] = ds.name
                context["dataset_columns"] = ds.column_names

        for ds_name, ds in config.datasets.items():
            context[f"dataset_{ds_name}"] = ds.name
        return context

    def _process_section(
        self,
        spec: TemplateSectionSpec,
        config: BuildConfig,
        index: int,
        build_log: BuildLog,
        ai_processor: AISectionProcessor | None,
    ) -> tuple[ReportSection, list[NumberClaim]]:
        """Process a single section based on its source type."""
        # Handle structural types that don't need processors
        if spec.type == "table_of_contents":
            return ReportSection(
                section_type=SectionType.TABLE_OF_CONTENTS,
                title=spec.title or "Table of Contents",
                level=spec.level,
            ), []

        if spec.source == SectionSource.STATIC:
            return process_static_section(spec)

        if spec.source == SectionSource.DATA:
            dataset = self._resolve_dataset(spec, config)
            # Transform data if needed
            processed_df = self.data_processor.process(dataset, spec)
            if processed_df is not dataset.dataframe:
                dataset = self._wrap_dataframe(dataset, processed_df)

            return process_data_table_section(spec, dataset, index)

        if spec.source == SectionSource.CHART:
            dataset = self._resolve_dataset(spec, config)
            # Transform data if needed
            processed_df = self.data_processor.process(dataset, spec)
            if processed_df is not dataset.dataframe:
                dataset = self._wrap_dataframe(dataset, processed_df)

            return process_chart_section(
                spec,
                dataset,
                config.theme,
                self.chart_engine,
            )

        if spec.source == SectionSource.AI_GENERATED:
            return self._process_ai_section(
                spec,
                config,
                build_log,
                ai_processor,
            )

        msg = f"Unknown section source: {spec.source}"  # type: ignore[unreachable]
        raise BuildError(msg)

    def _wrap_dataframe(self, original: Dataset, new_df: Any) -> Dataset:
        """Wrap a transformed dataframe in a new Dataset object.

        Args:
            original: The original Dataset object.
            new_df: The transformed pandas DataFrame.

        Returns:
            A new Dataset instance with the transformed data.
        """
        from pygramattic_reports.models import Dataset, Provenance

        # In a real implementation, we would regenerate the schema here
        # to match the new columns/dtypes. For now, we reuse the original
        # schema filtering for columns that still exist.
        new_schema = [col for col in original.schema if col.name in new_df.columns]

        return Dataset(
            id=f"{original.id}_processed",
            name=f"{original.name} (Processed)",
            schema=new_schema,
            dataframe=new_df,
            provenance=Provenance(
                source_type="transformation",
                source_name=original.provenance.source_name,
                loaded_at=original.provenance.loaded_at,
                normalized_at=now_utc(),
                row_count_raw=len(new_df),
                transformations=original.provenance.transformations + ["processed"],
            ),
            created_at=now_utc(),
        )

    def _process_ai_section(
        self,
        spec: TemplateSectionSpec,
        config: BuildConfig,
        build_log: BuildLog,
        ai_processor: AISectionProcessor | None,
    ) -> tuple[ReportSection, list[NumberClaim]]:
        """Process an AI-generated section with tracking."""
        if ai_processor and config.ai_enabled:
            build_log.ai_calls += 1
            try:
                return ai_processor.process(spec)
            except Exception as exc:
                build_log.ai_failures += 1
                _logger.warning(
                    "AI section failed, using placeholder",
                    error=str(exc),
                )
                return process_ai_placeholder_section(spec)
        return process_ai_placeholder_section(spec)

    def _create_ai_processor(
        self,
        config: BuildConfig,
    ) -> AISectionProcessor | None:
        """Create an AI processor if a Claude client is available."""
        if self.claude_client is None or not config.ai_enabled:
            return None

        from .ai_processor import AISectionProcessor as _Proc  # noqa: PLC0415

        return _Proc(
            client=self.claude_client,
            datasets=config.datasets,
            report_name=config.report_name,
        )

    def _resolve_dataset(
        self,
        spec: TemplateSectionSpec,
        config: BuildConfig,
    ) -> Any:  # noqa: ANN401
        """Resolve a dataset reference from section spec."""
        ds_name = spec.dataset or config.primary_dataset
        if not ds_name:
            msg = f"Section '{spec.title or spec.type}' requires a dataset but none specified"
            raise BuildError(msg)

        dataset = config.datasets.get(ds_name)
        if dataset is None:
            msg = f"Dataset '{ds_name}' not found. Available: {list(config.datasets.keys())}"
            raise BuildError(msg)
        return dataset

    @staticmethod
    def _is_recoverable(exc: Exception) -> bool:
        """Check if an exception is recoverable."""
        if isinstance(exc, PygramatticError):
            return exc.severity == ErrorSeverity.RECOVERABLE
        return False
