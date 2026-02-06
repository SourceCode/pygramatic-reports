"""Tests for AI section processor and builder AI integration (Phase 18)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd

from pygramattic_reports.builder import BuildConfig, ReportBuilder
from pygramattic_reports.builder.ai_processor import AISectionProcessor
from pygramattic_reports.charts import ChartEngine
from pygramattic_reports.exceptions import AIError
from pygramattic_reports.models import (
    SectionSource,
    SectionType,
    TemplateSectionSpec,
    TemplateSpec,
    ThemeSpec,
)
from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.models.dataset import ColumnSchema, Dataset, DataType, Provenance
from pygramattic_reports.templates import TemplateRenderer

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


def _mock_client(return_value: str = "AI generated content") -> MagicMock:
    """Create a mock ClaudeClient."""
    client = MagicMock()
    client.generate.return_value = return_value
    client.is_available.return_value = True
    client.enabled = True
    return client


def _build_config(
    sections: list[TemplateSectionSpec],
    datasets: dict[str, Dataset] | None = None,
    ai_enabled: bool = False,
) -> BuildConfig:
    """Create a BuildConfig for testing."""
    ds = _make_dataset()
    return BuildConfig(
        report_name="Test Report",
        template=TemplateSpec(name="test", sections=sections),
        theme=ThemeSpec(name="test"),
        datasets=datasets or {"main": ds},
        primary_dataset="main",
        ai_enabled=ai_enabled,
    )


# ---------- AISectionProcessor: summary generation --------------------------


class TestAiSummaryGeneration:
    """AI summary section produces content."""

    def test_ai_summary_uses_client(self) -> None:
        client = _mock_client("This is an executive summary.")
        ds = _make_dataset()
        processor = AISectionProcessor(client, {"main": ds}, "Test Report")

        spec = TemplateSectionSpec(
            type="summary",
            source=SectionSource.AI_GENERATED,
            title="Executive Summary",
        )
        section, claims = processor.process(spec)

        assert section.section_type == SectionType.SUMMARY
        assert section.content == "This is an executive summary."
        assert section.title == "Executive Summary"
        assert section.metadata.get("source") == "ai"
        assert claims == []
        client.generate.assert_called_once()


# ---------- AISectionProcessor: narrative generation -------------------------


class TestAiNarrativeGeneration:
    """AI narrative section produces content."""

    def test_ai_narrative_uses_client(self) -> None:
        client = _mock_client("Revenue trends show growth.")
        ds = _make_dataset()
        processor = AISectionProcessor(client, {"main": ds}, "Test Report")

        spec = TemplateSectionSpec(
            type="narrative",
            source=SectionSource.AI_GENERATED,
            title="Revenue Analysis",
        )
        section, _ = processor.process(spec)

        assert section.section_type == SectionType.NARRATIVE
        assert section.content == "Revenue trends show growth."
        assert section.metadata.get("source") == "ai"


# ---------- AISectionProcessor: fallback on failure --------------------------


class TestAiFallbackOnFailure:
    """When AI fails, fallback content is used."""

    def test_fallback_on_ai_error(self) -> None:
        client = _mock_client()
        client.generate.side_effect = AIError("Connection failed")
        ds = _make_dataset()
        processor = AISectionProcessor(client, {"main": ds}, "Test Report")

        spec = TemplateSectionSpec(
            type="summary",
            source=SectionSource.AI_GENERATED,
            title="Summary",
        )
        section, _ = processor.process(spec)

        assert section.content is not None
        assert len(section.content) > 0
        assert section.metadata.get("source") == "fallback"

    def test_fallback_narrative_on_error(self) -> None:
        client = _mock_client()
        client.generate.side_effect = AIError("Timeout")
        ds = _make_dataset()
        processor = AISectionProcessor(client, {"main": ds}, "Test Report")

        spec = TemplateSectionSpec(
            type="narrative",
            source=SectionSource.AI_GENERATED,
            title="Analysis",
        )
        section, _ = processor.process(spec)

        assert section.content is not None
        assert "3 records" in section.content
        assert section.metadata.get("source") == "fallback"

    def test_fallback_without_dataset(self) -> None:
        client = _mock_client()
        client.generate.side_effect = AIError("Failed")
        processor = AISectionProcessor(client, {}, "Test Report")

        spec = TemplateSectionSpec(
            type="summary",
            source=SectionSource.AI_GENERATED,
            title="No Data",
        )
        section, _ = processor.process(spec)

        assert "[Fallback]" in (section.content or "")


# ---------- AISectionProcessor: disabled uses placeholder --------------------


class TestAiDisabledUsesPlaceholder:
    """When disabled, placeholder content used."""

    def test_ai_disabled_returns_placeholder(self) -> None:
        config = _build_config(
            [
                TemplateSectionSpec(
                    type="summary",
                    source=SectionSource.AI_GENERATED,
                    title="Summary",
                    ai_prompt="Summarize the data",
                ),
            ],
            ai_enabled=False,
        )
        builder = ReportBuilder(
            chart_engine=ChartEngine(),
            template_renderer=TemplateRenderer(),
            claude_client=None,
        )
        report, _ = builder.build(config)

        assert len(report.sections) == 1
        assert "placeholder" in (report.sections[0].content or "").lower()


# ---------- AISectionProcessor: prompt includes data context -----------------


class TestAiPromptIncludesContext:
    """Prompt includes dataset sample."""

    def test_prompt_includes_data_sample(self) -> None:
        client = _mock_client("Summary text")
        ds = _make_dataset()
        processor = AISectionProcessor(client, {"main": ds}, "Test Report")

        spec = TemplateSectionSpec(
            type="summary",
            source=SectionSource.AI_GENERATED,
            title="Summary",
        )
        processor.process(spec)

        call_kwargs = client.generate.call_args
        context = call_kwargs.kwargs.get("context", "")
        assert "Data sample" in context
        assert "US" in context


# ---------- AISectionProcessor: prompt includes key stats --------------------


class TestAiPromptIncludesStats:
    """Summary prompt includes statistics."""

    def test_summary_prompt_includes_stats(self) -> None:
        client = _mock_client("Summary text")
        ds = _make_dataset()
        processor = AISectionProcessor(client, {"main": ds}, "Test Report")

        spec = TemplateSectionSpec(
            type="summary",
            source=SectionSource.AI_GENERATED,
            title="Summary",
        )
        processor.process(spec)

        call_kwargs = client.generate.call_args
        prompt = call_kwargs.kwargs.get("prompt", call_kwargs.args[0] if call_kwargs.args else "")
        assert "Test Report" in prompt
        assert "revenue" in prompt.lower() or "total" in prompt.lower()


# ---------- Builder with AI --------------------------------------------------


class TestBuilderWithAi:
    """Full builder produces report with AI sections."""

    def test_builder_with_ai_enabled(self) -> None:
        client = _mock_client("AI-generated executive summary.")
        ds = _make_dataset()
        config = BuildConfig(
            report_name="AI Report",
            template=TemplateSpec(
                name="test",
                sections=[
                    TemplateSectionSpec(
                        type="title",
                        source=SectionSource.STATIC,
                        content="Report",
                    ),
                    TemplateSectionSpec(
                        type="summary",
                        source=SectionSource.AI_GENERATED,
                        title="Summary",
                        ai_prompt="Summarize the data",
                    ),
                ],
            ),
            theme=ThemeSpec(name="test"),
            datasets={"main": ds},
            primary_dataset="main",
            ai_enabled=True,
        )

        builder = ReportBuilder(
            chart_engine=ChartEngine(),
            template_renderer=TemplateRenderer(),
            claude_client=client,
        )
        report, log = builder.build(config)

        assert len(report.sections) == 2
        assert report.sections[1].content == "AI-generated executive summary."
        assert log.ai_calls == 1
        assert log.ai_failures == 0


# ---------- Builder AI failure recoverable -----------------------------------


class TestBuilderAiFailureRecoverable:
    """AI failure doesn't crash the build."""

    def test_ai_exception_falls_back_to_placeholder(self) -> None:
        client = _mock_client()
        client.generate.side_effect = AIError("CLI crashed")
        ds = _make_dataset()
        config = BuildConfig(
            report_name="Fail Report",
            template=TemplateSpec(
                name="test",
                sections=[
                    TemplateSectionSpec(
                        type="title",
                        source=SectionSource.STATIC,
                        content="Report",
                    ),
                    TemplateSectionSpec(
                        type="summary",
                        source=SectionSource.AI_GENERATED,
                        title="Summary",
                    ),
                ],
            ),
            theme=ThemeSpec(name="test"),
            datasets={"main": ds},
            primary_dataset="main",
            ai_enabled=True,
        )

        builder = ReportBuilder(
            chart_engine=ChartEngine(),
            template_renderer=TemplateRenderer(),
            claude_client=client,
        )
        report, log = builder.build(config)

        # Build should succeed, using fallback content
        assert len(report.sections) == 2
        assert report.sections[1].content is not None
        assert log.ai_calls == 1
        assert log.status in ("completed", "completed_with_warnings")


# ---------- Build log tracks AI calls ----------------------------------------


class TestBuildLogTracksAiCalls:
    """Build log counts AI calls and failures."""

    def test_build_log_ai_counters(self) -> None:
        client = _mock_client()
        # First call succeeds, second fails (via AIError caught by processor)
        client.generate.side_effect = [
            "Generated summary",
            AIError("rate limited"),
        ]
        ds = _make_dataset()
        config = BuildConfig(
            report_name="Multi AI Report",
            template=TemplateSpec(
                name="test",
                sections=[
                    TemplateSectionSpec(
                        type="summary",
                        source=SectionSource.AI_GENERATED,
                        title="Summary 1",
                    ),
                    TemplateSectionSpec(
                        type="narrative",
                        source=SectionSource.AI_GENERATED,
                        title="Analysis",
                    ),
                ],
            ),
            theme=ThemeSpec(name="test"),
            datasets={"main": ds},
            primary_dataset="main",
            ai_enabled=True,
        )

        builder = ReportBuilder(
            chart_engine=ChartEngine(),
            template_renderer=TemplateRenderer(),
            claude_client=client,
        )
        report, log = builder.build(config)

        assert len(report.sections) == 2
        assert log.ai_calls == 2
        # The AIError is caught internally by AISectionProcessor,
        # so ai_failures stays 0 (only unexpected errors increment it)
        assert log.sections_generated == 2


# ---------- Custom prompt from template spec ---------------------------------


class TestCustomAiPrompt:
    """Custom ai_prompt from template spec is forwarded."""

    def test_custom_prompt_used(self) -> None:
        client = _mock_client("Custom response")
        ds = _make_dataset()
        processor = AISectionProcessor(client, {"main": ds}, "Test Report")

        spec = TemplateSectionSpec(
            type="narrative",
            source=SectionSource.AI_GENERATED,
            title="Custom",
            ai_prompt="Write about regional revenue distribution.",
        )
        processor.process(spec)

        call_kwargs = client.generate.call_args
        prompt = call_kwargs.kwargs.get("prompt", call_kwargs.args[0] if call_kwargs.args else "")
        assert "regional revenue distribution" in prompt
