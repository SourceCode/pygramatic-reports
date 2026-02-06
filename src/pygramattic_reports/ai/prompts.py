"""Prompt templates for Claude CLI content generation.

All prompts follow the PRD requirements:
- Concise
- Clear
- Professional tone
- High-school freshman reading level
- Avoid complex or technical wording
"""

from __future__ import annotations

SYSTEM_PROMPT = (
    "You are a professional report writer. Write clear, concise content "
    "suitable for business stakeholders. Use a professional but accessible tone. "
    "Write at a high-school freshman reading level. Avoid jargon and technical terms "
    "unless necessary. Be direct and factual."
)

SUMMARY_PROMPT = (
    'Write an executive summary for a report titled "{report_title}".\n'
    "\n"
    "The report analyzes the following data:\n"
    "{data_description}\n"
    "\n"
    "Key statistics:\n"
    "{key_stats}\n"
    "\n"
    "Write 2-3 paragraphs. Focus on the most important findings, trends, and "
    "takeaways. Do not include technical details about how the data was processed. "
    "Maximum {max_words} words."
)

NARRATIVE_PROMPT = (
    "Write an analysis section for a report.\n"
    "\n"
    "Topic: {topic}\n"
    "\n"
    "Data context:\n"
    "{data_context}\n"
    "\n"
    "{additional_context}\n"
    "\n"
    "Write a clear, detailed analysis. Highlight trends, comparisons, and "
    "actionable insights. Use specific numbers from the data. "
    "Maximum {max_words} words."
)

VALIDATION_PROMPT = (
    "You are a report validator. Compare the following report section "
    "against its source data and identify any discrepancies.\n"
    "\n"
    "Report section:\n"
    "{report_text}\n"
    "\n"
    "Source data:\n"
    "{source_data}\n"
    "\n"
    "Check for:\n"
    "1. Incorrect numbers\n"
    "2. Misleading descriptions of trends\n"
    "3. Claims not supported by the data\n"
    "4. Missing important context\n"
    "\n"
    'Respond with a JSON object:\n'
    '{{"valid": true/false, "issues": ["issue1", "issue2", ...]}}'
)

FEEDBACK_ANALYSIS_PROMPT = (
    "Compare the original report section with the edited version "
    "and identify what changed and why.\n"
    "\n"
    "Original:\n"
    "{original_text}\n"
    "\n"
    "Edited:\n"
    "{edited_text}\n"
    "\n"
    "For each change, explain:\n"
    "1. What was changed\n"
    "2. Why it was likely changed\n"
    "3. How future reports should be adjusted\n"
    "\n"
    "Respond with a JSON array of adjustment recommendations."
)


def format_data_description(
    dataset_name: str,
    columns: list[str],
    row_count: int,
) -> str:
    """Format a dataset description for inclusion in prompts.

    Args:
        dataset_name: Name of the dataset.
        columns: List of column names.
        row_count: Number of rows.

    Returns:
        Formatted description string.
    """
    return (
        f"Dataset: {dataset_name}\n"
        f"Columns: {', '.join(columns)}\n"
        f"Rows: {row_count}"
    )


def format_key_stats(stats: dict[str, float]) -> str:
    """Format key statistics for inclusion in prompts.

    Args:
        stats: Mapping of stat names to values.

    Returns:
        Formatted bullet-point string.
    """
    lines = [f"- {key}: {value}" for key, value in stats.items()]
    return "\n".join(lines)
