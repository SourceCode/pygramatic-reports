"""Claude CLI integration for AI-powered content generation.

Provides headless Claude CLI invocation with retry logic,
prompt templates, and fallback behavior.

Usage:
    from pygramattic_reports.ai import ClaudeClient

    client = ClaudeClient(config.claude)
    if client.is_available():
        text = client.generate("Summarize this data...", context="...")
"""

from .client import ClaudeClient
from .fallback import generate_fallback_narrative, generate_fallback_summary
from .prompts import NARRATIVE_PROMPT, SUMMARY_PROMPT, SYSTEM_PROMPT

__all__ = [
    "NARRATIVE_PROMPT",
    "SUMMARY_PROMPT",
    "SYSTEM_PROMPT",
    "ClaudeClient",
    "generate_fallback_narrative",
    "generate_fallback_summary",
]
