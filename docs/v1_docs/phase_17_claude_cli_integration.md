# Phase 17: Claude CLI Integration

## Objective

Build the `ClaudeClient` wrapper that provides a clean interface to Claude CLI for AI-powered content generation. This includes prompt templates, retry logic, fallback behavior, and response parsing.

## Why This Phase Is Seventeenth

The Claude CLI integration is an enhancement layer, not a core dependency. The entire report pipeline works without AI (Phase 13 uses placeholders). Building the AI client separately ensures clean separation and makes it testable with mocks.

## Tasks

### Task 17.1: Implement the ClaudeClient

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/ai/client.py`

**Description:** A subprocess-based client for headless Claude CLI calls with retry logic, timeout handling, and fallback behavior.

**Requirements (from PRD):**
- Headless subprocess calls
- Strict prompt templates
- Retries with exponential backoff
- Fallback summaries when AI fails
- Configurable timeout

```python
import subprocess
import time
from pygramattic_reports.config.settings import ClaudeConfig
from pygramattic_reports.exceptions import AIError
from pygramattic_reports.logging import get_logger

logger = get_logger("ai")


class ClaudeClient:
    """Client for Claude CLI headless invocations.

    Wraps subprocess calls to the Claude CLI with retry logic,
    timeout handling, and structured error management.

    Design principles:
    - Every AI call is optional. The system works without it.
    - Failures are logged and result in fallback content, not crashes.
    - All prompts are templated and deterministic (given the same input).

    Usage:
        client = ClaudeClient(config)
        result = client.generate(
            prompt="Summarize this data...",
            context="Revenue: US $1500, EU $2300...",
            max_tokens=512,
        )
    """

    def __init__(self, config: ClaudeConfig):
        self.config = config
        self.enabled = config.enabled

    def generate(
        self,
        prompt: str,
        context: str = "",
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> str:
        """Generate content using Claude CLI.

        Args:
            prompt: The user prompt
            context: Additional context (data, previous sections, etc.)
            max_tokens: Override max tokens
            system_prompt: Override system prompt

        Returns:
            Generated text content

        Raises:
            AIError: If all retries fail (severity=RETRIABLE)
        """
        if not self.enabled:
            logger.info("AI disabled, returning empty string")
            return ""

        full_prompt = self._build_prompt(prompt, context, system_prompt)
        max_tok = max_tokens or self.config.default_max_tokens

        last_error = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                result = self._invoke_cli(full_prompt, max_tok)
                logger.info("AI generation succeeded", attempt=attempt, prompt_len=len(full_prompt))
                return result
            except AIError as e:
                last_error = e
                if attempt < self.config.max_retries:
                    wait = self.config.retry_backoff_factor ** attempt
                    logger.warning(
                        "AI call failed, retrying",
                        attempt=attempt,
                        wait_seconds=wait,
                        error=str(e),
                    )
                    time.sleep(wait)

        logger.error("AI generation failed after all retries", retries=self.config.max_retries)
        raise AIError(
            f"Claude CLI failed after {self.config.max_retries} attempts: {last_error}",
        )

    def _invoke_cli(self, prompt: str, max_tokens: int) -> str:
        """Execute a single Claude CLI subprocess call.

        The exact CLI invocation depends on the Claude CLI version.
        This method should be adapted as the CLI interface evolves.
        """
        cmd = [
            self.config.executable,
            "--print",                   # Print response only, no interactive mode
            "--max-tokens", str(max_tokens),
            prompt,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
            )
            if result.returncode != 0:
                raise AIError(f"Claude CLI returned exit code {result.returncode}: {result.stderr}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise AIError(f"Claude CLI timed out after {self.config.timeout_seconds}s")
        except FileNotFoundError:
            raise AIError(f"Claude CLI not found at: {self.config.executable}")

    def _build_prompt(self, prompt: str, context: str, system_prompt: str | None) -> str:
        """Build the full prompt string for the CLI."""
        parts = []
        if system_prompt:
            parts.append(f"System: {system_prompt}\n\n")
        if context:
            parts.append(f"Context:\n{context}\n\n")
        parts.append(prompt)
        return "".join(parts)

    def is_available(self) -> bool:
        """Check if Claude CLI is available and functioning."""
        if not self.enabled:
            return False
        try:
            result = subprocess.run(
                [self.config.executable, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
```

---

### Task 17.2: Define Prompt Templates

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/ai/prompts.py`

**Description:** Strict, reusable prompt templates for each AI task. Prompts are designed per PRD requirements: concise, clear, professional tone, high-school freshman reading level.

```python
"""Prompt templates for Claude CLI content generation.

All prompts follow the PRD requirements:
- Concise
- Clear
- Professional tone
- High-school freshman reading level
- Avoid complex or technical wording
"""


SYSTEM_PROMPT = """You are a professional report writer. Write clear, concise content
suitable for business stakeholders. Use a professional but accessible tone.
Write at a high-school freshman reading level. Avoid jargon and technical terms
unless necessary. Be direct and factual."""


SUMMARY_PROMPT = """Write an executive summary for a report titled "{report_title}".

The report analyzes the following data:
{data_description}

Key statistics:
{key_stats}

Write 2-3 paragraphs. Focus on the most important findings, trends, and
takeaways. Do not include technical details about how the data was processed.
Maximum {max_words} words."""


NARRATIVE_PROMPT = """Write an analysis section for a report.

Topic: {topic}

Data context:
{data_context}

{additional_context}

Write a clear, detailed analysis. Highlight trends, comparisons, and
actionable insights. Use specific numbers from the data.
Maximum {max_words} words."""


VALIDATION_PROMPT = """You are a report validator. Compare the following report section
against its source data and identify any discrepancies.

Report section:
{report_text}

Source data:
{source_data}

Check for:
1. Incorrect numbers
2. Misleading descriptions of trends
3. Claims not supported by the data
4. Missing important context

Respond with a JSON object:
{{"valid": true/false, "issues": ["issue1", "issue2", ...]}}"""


FEEDBACK_ANALYSIS_PROMPT = """Compare the original report section with the edited version
and identify what changed and why.

Original:
{original_text}

Edited:
{edited_text}

For each change, explain:
1. What was changed
2. Why it was likely changed
3. How future reports should be adjusted

Respond with a JSON array of adjustment recommendations."""


def format_data_description(dataset_name: str, columns: list[str], row_count: int) -> str:
    """Format a dataset description for inclusion in prompts."""
    return (
        f"Dataset: {dataset_name}\n"
        f"Columns: {', '.join(columns)}\n"
        f"Rows: {row_count}"
    )


def format_key_stats(stats: dict[str, float]) -> str:
    """Format key statistics for inclusion in prompts."""
    lines = [f"- {key}: {value}" for key, value in stats.items()]
    return "\n".join(lines)
```

---

### Task 17.3: Implement the Fallback Generator

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/ai/fallback.py`

**Description:** Generates fallback content when Claude CLI is unavailable or fails. Produces basic, data-driven summaries without AI.

```python
import pandas as pd
from pygramattic_reports.models import Dataset


def generate_fallback_summary(
    dataset: Dataset,
    report_title: str,
    max_words: int = 200,
) -> str:
    """Generate a basic summary without AI.

    Produces a data-driven summary using simple statistics
    and predefined templates. Used when Claude CLI is unavailable.

    Args:
        dataset: The source dataset
        report_title: Report title for context
        max_words: Approximate target length

    Returns:
        A basic text summary
    """
    df = dataset.dataframe
    lines = [f"This report presents data from {dataset.name}."]
    lines.append(f"The dataset contains {dataset.row_count} records across {len(dataset.schema)} fields.")

    # Add basic stats for numeric columns
    numeric_cols = df.select_dtypes(include="number").columns
    if len(numeric_cols) > 0:
        lines.append("\nKey statistics:")
        for col in numeric_cols[:5]:  # Limit to 5 columns
            lines.append(
                f"- {col}: min={df[col].min():.2f}, max={df[col].max():.2f}, "
                f"avg={df[col].mean():.2f}"
            )

    return "\n".join(lines)


def generate_fallback_narrative(
    dataset: Dataset,
    topic: str = "",
) -> str:
    """Generate a basic narrative without AI."""
    df = dataset.dataframe
    lines = []
    if topic:
        lines.append(f"Analysis: {topic}")
    lines.append(f"\nThe dataset contains {dataset.row_count} records.")

    # Describe the data structure
    lines.append(f"Fields: {', '.join(dataset.column_names)}.")

    return "\n".join(lines)
```

---

### Task 17.4: Create AI Package Init

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/ai/__init__.py`

```python
"""Claude CLI integration for AI-powered content generation.

Usage:
    from pygramattic_reports.ai import ClaudeClient

    client = ClaudeClient(config.claude)
    if client.is_available():
        text = client.generate("Summarize this data...", context="...")
"""
from .client import ClaudeClient
from .prompts import SYSTEM_PROMPT, SUMMARY_PROMPT, NARRATIVE_PROMPT
from .fallback import generate_fallback_summary, generate_fallback_narrative

__all__ = [
    "ClaudeClient",
    "SYSTEM_PROMPT", "SUMMARY_PROMPT", "NARRATIVE_PROMPT",
    "generate_fallback_summary", "generate_fallback_narrative",
]
```

---

### Task 17.5: Write AI Client Tests

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_ai.py`

**Requirements:** Mock the subprocess calls. Do NOT call real Claude CLI in unit tests.

**Test cases:**
1. `test_generate_success` -- Mock successful subprocess call, verify response
2. `test_generate_retry_on_failure` -- Mock failure then success, verify retry
3. `test_generate_all_retries_exhausted` -- All retries fail, raises AIError
4. `test_generate_timeout` -- Subprocess timeout raises AIError
5. `test_generate_cli_not_found` -- Missing CLI raises AIError
6. `test_generate_disabled` -- When disabled, returns empty string
7. `test_is_available_true` -- Mock successful version check
8. `test_is_available_false` -- Mock missing CLI
9. `test_prompt_building` -- Full prompt includes system, context, and user prompt
10. `test_fallback_summary` -- Fallback produces basic data-driven summary
11. `test_fallback_narrative` -- Fallback produces basic narrative

**Example:**
```python
from unittest.mock import patch, MagicMock
from pygramattic_reports.ai import ClaudeClient
from pygramattic_reports.config.settings import ClaudeConfig


@patch("pygramattic_reports.ai.client.subprocess.run")
def test_generate_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="Generated summary text", stderr="")
    client = ClaudeClient(ClaudeConfig(enabled=True))
    result = client.generate("Summarize this data")
    assert result == "Generated summary text"
    assert mock_run.called


@patch("pygramattic_reports.ai.client.subprocess.run")
def test_generate_retry(mock_run):
    # First call fails, second succeeds
    mock_run.side_effect = [
        MagicMock(returncode=1, stdout="", stderr="rate limited"),
        MagicMock(returncode=0, stdout="Success", stderr=""),
    ]
    client = ClaudeClient(ClaudeConfig(enabled=True, retry_backoff_factor=0.01))
    result = client.generate("Test prompt")
    assert result == "Success"
    assert mock_run.call_count == 2
```

---

## Dependencies

- **Depends on:** Phase 03 (ClaudeConfig), Phase 04 (AIError, logging)
- **Blocks:** Phase 18 (Builder + AI), Phase 19 (Validator uses AI), Phase 20 (Feedback uses AI)

## Acceptance Criteria

1. `ClaudeClient.generate()` invokes Claude CLI and returns text
2. Retry logic works with exponential backoff
3. Timeout and missing CLI produce clear AIError exceptions
4. Fallback generator produces basic summaries without AI
5. Prompt templates follow PRD tone requirements
6. `is_available()` correctly detects CLI presence
7. All tests pass (with mocked subprocess)

## References

- PRD Claude CLI Integration: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 116-126)
- PRD Prompt characteristics: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 122-126)
- PRD Failure Handling: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 345-347)
- PRD Claude CLI Module: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 339-347)
