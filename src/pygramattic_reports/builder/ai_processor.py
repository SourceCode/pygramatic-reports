"""AI section processor for the report builder.

Processes AI-generated sections by invoking the Claude CLI
client with context-aware prompts. Falls back to basic
data-driven summaries when AI is unavailable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygramattic_reports.ai import (
    SUMMARY_PROMPT,
    SYSTEM_PROMPT,
    generate_fallback_narrative,
    generate_fallback_summary,
)
from pygramattic_reports.ai.prompts import format_data_description, format_key_stats
from pygramattic_reports.exceptions import AIError
from pygramattic_reports.logging import get_logger
from pygramattic_reports.models import (
    ReportSection,
    SectionType,
)
from pygramattic_reports.processors import aggregate

if TYPE_CHECKING:
    from pygramattic_reports.ai import ClaudeClient
    from pygramattic_reports.models import (
        Dataset,
        NumberClaim,
        TemplateSectionSpec,
    )

logger = get_logger("builder.ai")

_SECTION_TYPE_MAP: dict[str, SectionType] = {
    "summary": SectionType.SUMMARY,
    "narrative": SectionType.NARRATIVE,
    "title": SectionType.TITLE,
    "heading": SectionType.HEADING,
    "insight": SectionType.NARRATIVE,
    "anomaly": SectionType.NARRATIVE,
}


class AISectionProcessor:
    """Processes AI-generated report sections using Claude CLI.

    For each AI section in the template, this processor:

    1. Builds a context-aware prompt from the template spec and dataset
    2. Invokes Claude CLI via the ClaudeClient
    3. Parses the response into a ReportSection
    4. Falls back to a basic summary if AI fails

    Usage::

        processor = AISectionProcessor(claude_client, datasets, "My Report")
        section, claims = processor.process(section_spec)
    """

    def __init__(
        self,
        client: ClaudeClient,
        datasets: dict[str, Dataset],
        report_name: str,
    ) -> None:
        """Initialize with a Claude client and dataset references.

        Args:
            client: Claude CLI client instance.
            datasets: Name-to-Dataset mapping from build config.
            report_name: Report title for prompt context.
        """
        self.client = client
        self.datasets = datasets
        self.report_name = report_name

    def process(
        self,
        spec: TemplateSectionSpec,
    ) -> tuple[ReportSection, list[NumberClaim]]:
        """Process an AI-generated section.

        Attempts Claude CLI generation. On failure, produces fallback content.

        Args:
            spec: The template section spec with AI prompt.

        Returns:
            Tuple of (ReportSection with AI content, list of NumberClaims).
        """
        section_type = _SECTION_TYPE_MAP.get(spec.type, SectionType.NARRATIVE)
        dataset = self._resolve_dataset(spec.dataset)

        prompt = self._build_prompt(spec, dataset)

        try:
            content = self.client.generate(
                prompt=prompt,
                context=self._build_context(dataset),
                system_prompt=SYSTEM_PROMPT,
            )
            logger.info(
                "AI section generated",
                section_type=spec.type,
                length=len(content),
            )
            source_tag = "ai"
        except AIError as exc:
            logger.warning(
                "AI generation failed, using fallback",
                error=str(exc),
            )
            content = self._generate_fallback(spec, dataset)
            source_tag = "fallback"

        return (
            ReportSection(
                section_type=section_type,
                title=spec.title,
                content=content,
                metadata={"source": source_tag},
            ),
            [],
        )

    def _build_prompt(
        self,
        spec: TemplateSectionSpec,
        dataset: Dataset | None,
    ) -> str:
        """Build the prompt from the template spec and dataset context."""
        if spec.ai_prompt:
            return spec.ai_prompt

        if spec.type == "summary":
            return self._build_summary_prompt(spec, dataset)

        if spec.type == "narrative":
            return self._build_narrative_prompt(spec, dataset)

        if spec.type == "insight":
            return self._build_insight_prompt(spec, dataset)

        if spec.type == "anomaly":
            return self._build_anomaly_prompt(spec, dataset)

        return f"Write content for a {spec.type} section."

    def _build_summary_prompt(
        self,
        spec: TemplateSectionSpec,
        dataset: Dataset | None,
    ) -> str:
        """Build prompt for summary-type sections."""
        data_desc = ""
        key_stats = ""
        if dataset:
            data_desc = format_data_description(
                dataset.name,
                dataset.column_names,
                dataset.row_count,
            )
            key_stats = self._compute_key_stats(dataset)
        return SUMMARY_PROMPT.format(
            report_title=self.report_name,
            data_description=data_desc,
            key_stats=key_stats,
            max_words=spec.ai_max_words or 200,
        )

    def _build_narrative_prompt(
        self,
        spec: TemplateSectionSpec,
        dataset: Dataset | None,
    ) -> str:
        """Build prompt for narrative-type sections."""
        from pygramattic_reports.ai.prompts import NARRATIVE_PROMPT  # noqa: PLC0415

        data_context = ""
        if dataset:
            data_context = self._format_sample_data(dataset)
        return NARRATIVE_PROMPT.format(
            topic=spec.title or "Data Analysis",
            data_context=data_context,
            additional_context=spec.ai_context or "",
            max_words=spec.ai_max_words or 300,
        )

    def _build_insight_prompt(
        self,
        spec: TemplateSectionSpec,
        dataset: Dataset | None,
    ) -> str:
        """Build prompt for insight-type sections."""
        from pygramattic_reports.ai.prompts import INSIGHT_PROMPT

        data_context = ""
        if dataset:
            data_context = self._format_sample_data(dataset)
        return INSIGHT_PROMPT.format(
            topic=spec.title or "Key Insights",
            data_context=data_context,
            additional_context=spec.ai_context or "",
            max_words=spec.ai_max_words or 200,
        )

    def _build_anomaly_prompt(
        self,
        spec: TemplateSectionSpec,
        dataset: Dataset | None,
    ) -> str:
        """Build prompt for anomaly-type sections."""
        from pygramattic_reports.ai.prompts import ANOMALY_PROMPT

        data_context = ""
        if dataset:
            data_context = self._format_sample_data(dataset)
        return ANOMALY_PROMPT.format(
            topic=spec.title or "Anomaly Detection",
            data_context=data_context,
            additional_context=spec.ai_context or "",
            max_words=spec.ai_max_words or 200,
        )

    def _build_context(self, dataset: Dataset | None) -> str:
        """Build data context string for the AI prompt."""
        if dataset is None:
            return ""

        df = dataset.dataframe
        sample = df.head(10).to_string(index=False)
        return f"Data sample (first {min(10, len(df))} of {len(df)} rows):\n{sample}"

    def _compute_key_stats(self, dataset: Dataset) -> str:
        """Compute basic statistics for numeric columns."""
        stats: dict[str, float] = {}
        numeric_cols = dataset.dataframe.select_dtypes(include="number").columns
        for col in numeric_cols[:5]:
            try:
                stats[f"{col} (total)"] = aggregate(dataset, col, "sum")
                stats[f"{col} (avg)"] = aggregate(dataset, col, "avg")
            except Exception:
                logger.debug("Skipping stats for column %s", col)
        return format_key_stats(stats)

    @staticmethod
    def _format_sample_data(dataset: Dataset) -> str:
        """Format a data sample for inclusion in prompts."""
        return dataset.dataframe.head(20).to_string(index=False)

    def _generate_fallback(
        self,
        spec: TemplateSectionSpec,
        dataset: Dataset | None,
    ) -> str:
        """Generate fallback content when AI fails."""
        if dataset is None:
            return f"[Fallback] Content for '{spec.title or spec.type}' section."

        if spec.type == "summary":
            return generate_fallback_summary(
                dataset,
                self.report_name,
                spec.ai_max_words or 200,
            )
        return generate_fallback_narrative(dataset, spec.title or "")

    def _resolve_dataset(self, dataset_name: str | None) -> Dataset | None:
        """Resolve a dataset reference from the template."""
        if dataset_name is None:
            if self.datasets:
                return next(iter(self.datasets.values()))
            return None
        return self.datasets.get(dataset_name)
