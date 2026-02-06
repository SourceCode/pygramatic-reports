# Phase 18: AI-Powered Report Sections

## Objective

Integrate the Claude CLI client (Phase 17) into the Report Builder (Phase 13) to enable AI-generated content: executive summaries, narrative analysis, and section drafting. Replace the placeholder AI sections with real Claude CLI calls.

## Why This Phase Is Eighteenth

The Builder works end-to-end with placeholders for AI sections. The Claude CLI client is tested and ready. This phase connects them, enabling the full report generation experience with AI-powered narratives.

## Tasks

### Task 18.1: Implement the AI Section Processor

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/builder/ai_processor.py`

**Description:** Processes AI-generated sections by invoking the Claude CLI client with context-aware prompts.

```python
from pygramattic_reports.models import (
    ReportSection, SectionType, NumberClaim,
    TemplateSectionSpec, Dataset, ThemeSpec,
)
from pygramattic_reports.ai import (
    ClaudeClient, SYSTEM_PROMPT, SUMMARY_PROMPT, NARRATIVE_PROMPT,
    generate_fallback_summary, generate_fallback_narrative,
)
from pygramattic_reports.ai.prompts import format_data_description, format_key_stats
from pygramattic_reports.processors import aggregate
from pygramattic_reports.exceptions import AIError
from pygramattic_reports.logging import get_logger

logger = get_logger("builder.ai")


class AISectionProcessor:
    """Processes AI-generated report sections using Claude CLI.

    For each AI section in the template, this processor:
    1. Builds a context-aware prompt from the template spec and dataset
    2. Invokes Claude CLI via the ClaudeClient
    3. Parses the response into a ReportSection
    4. Falls back to a basic summary if AI fails

    Usage:
        processor = AISectionProcessor(claude_client, datasets)
        section, claims = processor.process(section_spec)
    """

    def __init__(
        self,
        client: ClaudeClient,
        datasets: dict[str, Dataset],
        report_name: str,
    ):
        self.client = client
        self.datasets = datasets
        self.report_name = report_name

    def process(
        self, spec: TemplateSectionSpec
    ) -> tuple[ReportSection, list[NumberClaim]]:
        """Process an AI-generated section.

        Attempts Claude CLI generation. On failure, produces fallback content.

        Args:
            spec: The template section spec with AI prompt

        Returns:
            Tuple of (ReportSection with AI content, list of NumberClaims)
        """
        section_type = self._map_section_type(spec.type)
        dataset = self._resolve_dataset(spec.dataset)

        # Build the prompt
        prompt = self._build_prompt(spec, dataset)

        try:
            content = self.client.generate(
                prompt=prompt,
                context=self._build_context(dataset),
                system_prompt=SYSTEM_PROMPT,
            )
            logger.info("AI section generated", section_type=spec.type, length=len(content))
        except AIError as e:
            logger.warning("AI generation failed, using fallback", error=str(e))
            content = self._generate_fallback(spec, dataset)

        return ReportSection(
            section_type=section_type,
            title=spec.title,
            content=content,
            metadata={"source": "ai" if not isinstance(content, str) or "[Fallback]" not in content else "fallback"},
        ), []

    def _build_prompt(self, spec: TemplateSectionSpec, dataset: Dataset | None) -> str:
        """Build the prompt from the template spec and dataset context."""
        if spec.ai_prompt:
            # Use the custom prompt from the template
            prompt = spec.ai_prompt
        elif spec.type == "summary":
            # Use the summary template
            data_desc = ""
            key_stats = ""
            if dataset:
                data_desc = format_data_description(
                    dataset.name, dataset.column_names, dataset.row_count
                )
                key_stats = self._compute_key_stats(dataset)
            prompt = SUMMARY_PROMPT.format(
                report_title=self.report_name,
                data_description=data_desc,
                key_stats=key_stats,
                max_words=spec.ai_max_words or 200,
            )
        elif spec.type == "narrative":
            data_context = ""
            if dataset:
                data_context = self._format_sample_data(dataset)
            prompt = NARRATIVE_PROMPT.format(
                topic=spec.title or "Data Analysis",
                data_context=data_context,
                additional_context=spec.ai_context or "",
                max_words=spec.ai_max_words or 300,
            )
        else:
            prompt = spec.ai_prompt or f"Write content for a {spec.type} section."

        return prompt

    def _build_context(self, dataset: Dataset | None) -> str:
        """Build data context string for the AI prompt."""
        if dataset is None:
            return ""

        # Include a sample of the data (first 10 rows as formatted text)
        df = dataset.dataframe
        sample = df.head(10).to_string(index=False)
        return f"Data sample (first {min(10, len(df))} of {len(df)} rows):\n{sample}"

    def _compute_key_stats(self, dataset: Dataset) -> str:
        """Compute basic statistics for numeric columns."""
        stats = {}
        numeric_cols = dataset.dataframe.select_dtypes(include="number").columns
        for col in numeric_cols[:5]:
            try:
                stats[f"{col} (total)"] = aggregate(dataset, col, "sum")
                stats[f"{col} (avg)"] = aggregate(dataset, col, "avg")
            except Exception:
                pass
        return format_key_stats(stats)

    def _format_sample_data(self, dataset: Dataset) -> str:
        """Format a data sample for inclusion in prompts."""
        return dataset.dataframe.head(20).to_string(index=False)

    def _generate_fallback(self, spec: TemplateSectionSpec, dataset: Dataset | None) -> str:
        """Generate fallback content when AI fails."""
        if dataset is None:
            return f"[Fallback] Content for '{spec.title or spec.type}' section."

        if spec.type == "summary":
            return generate_fallback_summary(
                dataset, self.report_name, spec.ai_max_words or 200
            )
        else:
            return generate_fallback_narrative(
                dataset, spec.title or ""
            )

    def _resolve_dataset(self, dataset_name: str | None) -> Dataset | None:
        """Resolve a dataset reference from the template."""
        if dataset_name is None:
            # Use the first dataset as default
            if self.datasets:
                return next(iter(self.datasets.values()))
            return None
        return self.datasets.get(dataset_name)

    def _map_section_type(self, type_str: str) -> SectionType:
        """Map template section type string to SectionType enum."""
        mapping = {
            "summary": SectionType.SUMMARY,
            "narrative": SectionType.NARRATIVE,
            "title": SectionType.TITLE,
            "heading": SectionType.HEADING,
        }
        return mapping.get(type_str, SectionType.NARRATIVE)
```

---

### Task 18.2: Update the Report Builder to Use AI Processor

**File to update:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/builder/builder.py`

**Description:** Modify `ReportBuilder` to accept a `ClaudeClient` and use `AISectionProcessor` for AI-generated sections instead of placeholders.

**Changes:**
- Add `claude_client: ClaudeClient | None` to `__init__`
- In `_process_section`, when `section_spec.source == SectionSource.AI_GENERATED`:
  - If `claude_client` is not None and `build_config.ai_enabled`:
    - Use `AISectionProcessor.process()`
    - Track AI calls in build log
  - Else: use placeholder (existing behavior)
- Update build log tracking: `ai_calls`, `ai_failures`

**Key code change:**
```python
def _process_section(self, section_spec, config, index):
    match section_spec.source:
        case SectionSource.STATIC:
            return process_static_section(section_spec)
        case SectionSource.DATA:
            dataset = config.datasets.get(section_spec.dataset)
            if not dataset:
                raise BuildError(f"Dataset not found: {section_spec.dataset}")
            return process_data_table_section(section_spec, dataset)
        case SectionSource.CHART:
            dataset = config.datasets.get(section_spec.dataset)
            if not dataset:
                raise BuildError(f"Dataset not found: {section_spec.dataset}")
            return process_chart_section(section_spec, dataset, config.theme, self.chart_engine)
        case SectionSource.AI_GENERATED:
            if self.ai_processor and config.ai_enabled:
                self.build_log.ai_calls += 1
                try:
                    return self.ai_processor.process(section_spec)
                except Exception as e:
                    self.build_log.ai_failures += 1
                    raise
            else:
                return process_ai_placeholder_section(section_spec)
```

---

### Task 18.3: Update the `build` CLI Command for AI

**File to update:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/cli/build_cmd.py`

**Changes:**
- When `--no-ai` is NOT set and config has `ai.enabled: true`:
  - Initialize `ClaudeClient` from app config
  - Check `client.is_available()` -- if not available, warn and proceed without AI
  - Pass client to `ReportBuilder`
- Show AI status in build progress:
  ```
  AI: Enabled (Claude CLI available)
  -- or --
  AI: Disabled (--no-ai flag)
  -- or --
  AI: Unavailable (Claude CLI not found, using fallbacks)
  ```

---

### Task 18.4: Write AI Integration Tests

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_ai_processor.py`

**Test cases (all with mocked Claude CLI):**
1. `test_ai_summary_generation` -- AI summary section produces content
2. `test_ai_narrative_generation` -- AI narrative section produces content
3. `test_ai_fallback_on_failure` -- When AI fails, fallback content is used
4. `test_ai_disabled_uses_placeholder` -- When disabled, placeholder content used
5. `test_ai_prompt_includes_data_context` -- Prompt includes dataset sample
6. `test_ai_prompt_includes_key_stats` -- Summary prompt includes statistics
7. `test_builder_with_ai` -- Full builder produces report with AI sections
8. `test_builder_ai_failure_recoverable` -- AI failure doesn't crash the build
9. `test_build_log_tracks_ai_calls` -- Build log counts AI calls and failures

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/integration/test_ai_build.py`

**Integration test (with mocked CLI):**
1. `test_full_pipeline_with_ai` -- Ingest CSV → build with AI enabled (mocked) → verify AI sections have content
2. `test_full_pipeline_ai_unavailable` -- Ingest → build → AI unavailable → fallback content used, report still generated

---

## Dependencies

- **Depends on:** Phase 13 (Builder), Phase 17 (Claude CLI client)
- **Blocks:** Phase 19 (Validator uses AI for narrative checking)

## Acceptance Criteria

1. AI-generated sections contain Claude CLI output (when mocked client returns content)
2. Fallback content is used when AI fails
3. Build log tracks AI calls and failures
4. `--no-ai` flag disables AI sections
5. Missing Claude CLI produces a warning, not a crash
6. All tests pass (with mocked subprocess)

## References

- PRD Claude CLI Integration: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 116-126)
- PRD Prompt characteristics: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 122-126)
- PRD Report Builder: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 108-143)
