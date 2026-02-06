"""Core report builder for pygramattic-reports.

Assembles reports from templates, themes, and datasets by
orchestrating section processors and the chart engine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pygramattic_reports.exceptions import BuildError, ErrorSeverity, PygramatticError
from pygramattic_reports.logging import BuildLog, get_logger
from pygramattic_reports.models import (
    Report,
    SectionSource,
    generate_id,
    now_utc,
)

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
        NumberClaim,
        ReportSection,
        TemplateSectionSpec,
    )
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

    Usage::

        builder = ReportBuilder(
            chart_engine=ChartEngine(),
            template_renderer=TemplateRenderer(),
            claude_client=client,  # optional
        )
        report, build_log = builder.build(build_config)
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

    def build(
        self, config: BuildConfig,
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
            build_id=generate_id(), started_at=now_utc(),
        )

        ai_processor = self._create_ai_processor(config)

        context = self._build_context(config)
        resolved_sections = self.template_renderer.resolve_template(
            config.template, context,
        )

        report_sections: list[ReportSection] = []
        number_claims: list[NumberClaim] = []

        for i, section_spec in enumerate(resolved_sections):
            try:
                section, claims = self._process_section(
                    section_spec, config, i, build_log, ai_processor,
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
                        "warning", "builder",
                        f"Section {i} skipped: {exc}",
                    )
                    build_log.sections_skipped += 1
                else:
                    build_log.finalize("failed")
                    raise

        status = (
            "completed"
            if build_log.sections_skipped == 0
            else "completed_with_warnings"
        )
        build_log.finalize(status)

        report = Report(
            id=generate_id(),
            name=config.report_name,
            sections=report_sections,
            number_claims=number_claims,
            datasets_used=[
                ds.id for ds in config.datasets.values()
            ],
            template_name=config.template.name,
            theme_name=config.theme.name,
            build_timestamp=now_utc(),
            build_warnings=[
                e.message
                for e in build_log.entries
                if e.level == "warning"
            ],
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
        if spec.source == SectionSource.STATIC:
            return process_static_section(spec)

        if spec.source == SectionSource.DATA:
            dataset = self._resolve_dataset(spec, config)
            return process_data_table_section(spec, dataset, index)

        if spec.source == SectionSource.CHART:
            dataset = self._resolve_dataset(spec, config)
            return process_chart_section(
                spec, dataset, config.theme, self.chart_engine,
            )

        if spec.source == SectionSource.AI_GENERATED:
            return self._process_ai_section(
                spec, config, build_log, ai_processor,
            )

        msg = f"Unknown section source: {spec.source}"  # type: ignore[unreachable]
        raise BuildError(msg)

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

    @staticmethod
    def _resolve_dataset(
        spec: TemplateSectionSpec,
        config: BuildConfig,
    ) -> Any:  # noqa: ANN401
        """Resolve a dataset reference from section spec."""
        ds_name = spec.dataset or config.primary_dataset
        if not ds_name:
            msg = (
                f"Section '{spec.title or spec.type}' requires "
                f"a dataset but none specified"
            )
            raise BuildError(msg)

        dataset = config.datasets.get(ds_name)
        if dataset is None:
            msg = (
                f"Dataset '{ds_name}' not found. "
                f"Available: {list(config.datasets.keys())}"
            )
            raise BuildError(msg)
        return dataset

    @staticmethod
    def _is_recoverable(exc: Exception) -> bool:
        """Check if an exception is recoverable."""
        if isinstance(exc, PygramatticError):
            return exc.severity == ErrorSeverity.RECOVERABLE
        return False
