"""Unit tests for AI client, prompts, and fallback (Phase 17)."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from pygramattic_reports.ai import (
    NARRATIVE_PROMPT,
    SUMMARY_PROMPT,
    SYSTEM_PROMPT,
    ClaudeClient,
    generate_fallback_narrative,
    generate_fallback_summary,
)
from pygramattic_reports.ai.prompts import (
    format_data_description,
    format_key_stats,
)
from pygramattic_reports.config.settings import ClaudeConfig
from pygramattic_reports.exceptions import AIError

# ---------- Helpers ----------------------------------------------------------


def _make_dataset(
    name: str = "test_data",
    data: dict | None = None,
) -> MagicMock:
    """Create a mock Dataset with a real DataFrame."""
    from pygramattic_reports.models.dataset import ColumnSchema, DataType  # noqa: PLC0415

    if data is None:
        data = {"region": ["US", "EU", "APAC"], "revenue": [1500, 2300, 890]}

    df = pd.DataFrame(data)
    schema = [
        ColumnSchema(
            name=col,
            dtype=DataType.STRING if df[col].dtype == "object" else DataType.FLOAT,
        )
        for col in df.columns
    ]

    mock = MagicMock()
    mock.name = name
    mock.dataframe = df
    mock.schema = schema
    mock.column_names = list(df.columns)
    mock.row_count = len(df)
    return mock


def _fast_config(**kwargs: object) -> ClaudeConfig:
    """Create a ClaudeConfig with fast retry for testing."""
    defaults: dict[str, object] = {
        "enabled": True,
        "retry_backoff_factor": 0.01,
        "max_retries": 3,
    }
    defaults.update(kwargs)
    return ClaudeConfig(**defaults)  # type: ignore[arg-type]


# ---------- ClaudeClient.generate success ------------------------------------


class TestGenerateSuccess:
    """Successful AI generation."""

    @patch("pygramattic_reports.ai.client.subprocess.run")
    def test_generate_returns_stripped_output(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(
            returncode=0, stdout="Generated summary text\n", stderr="",
        )
        client = ClaudeClient(_fast_config())
        result = client.generate("Summarize this data")
        assert result == "Generated summary text"
        assert mock_run.called


# ---------- ClaudeClient.generate retry --------------------------------------


class TestGenerateRetry:
    """Retry logic with exponential backoff."""

    @patch("pygramattic_reports.ai.client.subprocess.run")
    def test_retries_on_failure_then_succeeds(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="rate limited"),
            MagicMock(returncode=0, stdout="Success", stderr=""),
        ]
        client = ClaudeClient(_fast_config(max_retries=3))
        result = client.generate("Test prompt")
        assert result == "Success"
        assert mock_run.call_count == 2


# ---------- ClaudeClient.generate all retries exhausted ----------------------


class TestGenerateRetriesExhausted:
    """All retries fail, raises AIError."""

    @patch("pygramattic_reports.ai.client.subprocess.run")
    def test_raises_after_all_retries(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="error",
        )
        client = ClaudeClient(_fast_config(max_retries=2))
        with pytest.raises(AIError, match="failed after 2 attempts"):
            client.generate("Test prompt")
        assert mock_run.call_count == 2


# ---------- ClaudeClient.generate timeout ------------------------------------


class TestGenerateTimeout:
    """Subprocess timeout raises AIError."""

    @patch("pygramattic_reports.ai.client.subprocess.run")
    def test_timeout_raises_ai_error(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=120)
        client = ClaudeClient(_fast_config(max_retries=1))
        with pytest.raises(AIError, match="timed out"):
            client.generate("Test prompt")


# ---------- ClaudeClient.generate CLI not found ------------------------------


class TestGenerateCliNotFound:
    """Missing CLI raises AIError."""

    @patch("pygramattic_reports.ai.client.subprocess.run")
    def test_missing_cli_raises_ai_error(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = FileNotFoundError("No such file")
        client = ClaudeClient(_fast_config(max_retries=1))
        with pytest.raises(AIError, match="not found"):
            client.generate("Test prompt")


# ---------- ClaudeClient.generate disabled -----------------------------------


class TestGenerateDisabled:
    """When disabled, returns empty string."""

    def test_disabled_returns_empty(self) -> None:
        client = ClaudeClient(_fast_config(enabled=False))
        result = client.generate("Summarize this data")
        assert result == ""


# ---------- ClaudeClient.is_available ----------------------------------------


class TestIsAvailable:
    """Claude CLI availability detection."""

    @patch("pygramattic_reports.ai.client.subprocess.run")
    def test_available_when_version_succeeds(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        client = ClaudeClient(_fast_config())
        assert client.is_available() is True

    @patch("pygramattic_reports.ai.client.subprocess.run")
    def test_unavailable_when_not_found(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = FileNotFoundError
        client = ClaudeClient(_fast_config())
        assert client.is_available() is False

    @patch("pygramattic_reports.ai.client.subprocess.run")
    def test_unavailable_when_nonzero_exit(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1)
        client = ClaudeClient(_fast_config())
        assert client.is_available() is False

    def test_unavailable_when_disabled(self) -> None:
        client = ClaudeClient(_fast_config(enabled=False))
        assert client.is_available() is False


# ---------- Prompt building --------------------------------------------------


class TestPromptBuilding:
    """Full prompt includes system, context, and user prompt."""

    def test_full_prompt_with_all_parts(self) -> None:
        client = ClaudeClient(_fast_config(enabled=False))
        result = client._build_prompt(
            prompt="Summarize data",
            context="Revenue: US $1500",
            system_prompt="Be concise",
        )
        assert "System: Be concise" in result
        assert "Context:\nRevenue: US $1500" in result
        assert "Summarize data" in result

    def test_prompt_without_system_or_context(self) -> None:
        client = ClaudeClient(_fast_config(enabled=False))
        result = client._build_prompt(
            prompt="Just the prompt",
            context="",
            system_prompt=None,
        )
        assert result == "Just the prompt"
        assert "System:" not in result
        assert "Context:" not in result


# ---------- Prompt templates -------------------------------------------------


class TestPromptTemplates:
    """Prompt templates are valid format strings."""

    def test_system_prompt_is_nonempty(self) -> None:
        assert len(SYSTEM_PROMPT) > 0

    def test_summary_prompt_has_placeholders(self) -> None:
        result = SUMMARY_PROMPT.format(
            report_title="Test Report",
            data_description="Test data",
            key_stats="- revenue: 1500",
            max_words=200,
        )
        assert "Test Report" in result
        assert "Test data" in result

    def test_narrative_prompt_has_placeholders(self) -> None:
        result = NARRATIVE_PROMPT.format(
            topic="Sales Analysis",
            data_context="Revenue data",
            additional_context="Q4 focus",
            max_words=300,
        )
        assert "Sales Analysis" in result

    def test_format_data_description(self) -> None:
        result = format_data_description("sales", ["region", "revenue"], 100)
        assert "sales" in result
        assert "region" in result
        assert "100" in result

    def test_format_key_stats(self) -> None:
        result = format_key_stats({"revenue": 1500.0, "cost": 800.0})
        assert "- revenue: 1500.0" in result
        assert "- cost: 800.0" in result


# ---------- Fallback summary -------------------------------------------------


class TestFallbackSummary:
    """Fallback produces basic data-driven summary."""

    def test_fallback_summary_includes_name_and_stats(self) -> None:
        ds = _make_dataset(name="sales_data")
        result = generate_fallback_summary(ds, report_title="Sales Report")
        assert "sales_data" in result
        assert "3 records" in result
        assert "2 fields" in result
        assert "revenue" in result
        assert "min=" in result
        assert "max=" in result

    def test_fallback_summary_no_numeric_columns(self) -> None:
        ds = _make_dataset(data={"name": ["Alice", "Bob"], "city": ["NY", "LA"]})
        result = generate_fallback_summary(ds)
        assert "2 records" in result
        assert "min=" not in result


# ---------- Fallback narrative -----------------------------------------------


class TestFallbackNarrative:
    """Fallback produces basic narrative."""

    def test_fallback_narrative_with_topic(self) -> None:
        ds = _make_dataset()
        result = generate_fallback_narrative(ds, topic="Revenue Analysis")
        assert "Revenue Analysis" in result
        assert "3 records" in result
        assert "region" in result

    def test_fallback_narrative_without_topic(self) -> None:
        ds = _make_dataset()
        result = generate_fallback_narrative(ds)
        assert "Analysis:" not in result
        assert "3 records" in result
