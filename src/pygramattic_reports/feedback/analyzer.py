"""Feedback analyzer for report improvement recommendations.

Analyzes diffs between original and edited reports to produce
actionable recommendations. Uses AI when available, with
rule-based fallback.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pygramattic_reports.ai.prompts import FEEDBACK_ANALYSIS_PROMPT
from pygramattic_reports.exceptions import AIError, FeedbackError
from pygramattic_reports.logging import get_logger

if TYPE_CHECKING:
    from pygramattic_reports.ai import ClaudeClient

    from .differ import ReportDiff

logger = get_logger("feedback")


@dataclass
class FeedbackRecommendation:
    """A single recommendation for improving future reports.

    Attributes:
        category: Recommendation category (e.g. ``"conciseness"``).
        section: Which section this applies to.
        description: What should change.
        priority: One of ``"high"``, ``"medium"``, ``"low"``.
    """

    category: str
    section: str
    description: str
    priority: str = "medium"


@dataclass
class FeedbackReport:
    """Complete feedback analysis.

    Attributes:
        diff: The underlying report diff.
        recommendations: Actionable improvement suggestions.
        ai_analysis: Raw AI analysis text, if available.
    """

    diff: ReportDiff
    recommendations: list[FeedbackRecommendation] = field(default_factory=list)
    ai_analysis: str | None = None


class FeedbackAnalyzer:
    """Analyzes report diffs and produces improvement recommendations.

    For V1, feedback produces recommendations for human review.
    It does NOT automatically modify templates or prompts.

    Usage::

        analyzer = FeedbackAnalyzer(claude_client)
        feedback = analyzer.analyze(diff)
    """

    def __init__(self, client: ClaudeClient | None = None) -> None:
        """Initialize with optional Claude client.

        Args:
            client: Claude CLI client for AI-powered analysis,
                or None for rule-based only.
        """
        self.client = client

    def analyze(self, diff: ReportDiff) -> FeedbackReport:
        """Analyze a diff and produce recommendations.

        If Claude CLI is available, uses AI for intelligent analysis.
        Otherwise, produces basic rule-based recommendations.

        Args:
            diff: Structured diff to analyze.

        Returns:
            Complete feedback report with recommendations.
        """
        recommendations: list[FeedbackRecommendation] = []

        recommendations.extend(self._basic_analysis(diff))

        ai_analysis = None
        if self.client and self.client.is_available() and diff.entries:
            try:
                ai_analysis, ai_recs = self._ai_analysis(diff)
                recommendations.extend(ai_recs)
            except (AIError, FeedbackError) as exc:
                logger.warning(
                    "AI feedback analysis failed",
                    error=str(exc),
                )

        return FeedbackReport(
            diff=diff,
            recommendations=recommendations,
            ai_analysis=ai_analysis,
        )

    @staticmethod
    def _basic_analysis(diff: ReportDiff) -> list[FeedbackRecommendation]:
        """Rule-based analysis of common feedback patterns."""
        recommendations: list[FeedbackRecommendation] = []

        for entry in diff.entries:
            if (
                entry.change_type == "modified"
                and len(entry.edited) < len(entry.original) * 0.7
            ):
                recommendations.append(FeedbackRecommendation(
                    category="conciseness",
                    section=entry.section,
                    description=(
                        "Content was shortened significantly. "
                        "Consider reducing verbosity in future generation."
                    ),
                    priority="medium",
                ))

            if (
                entry.change_type == "modified"
                and len(entry.edited) > len(entry.original) * 1.5
            ):
                recommendations.append(FeedbackRecommendation(
                    category="detail",
                    section=entry.section,
                    description=(
                        "Content was expanded. "
                        "Consider adding more detail in future generation."
                    ),
                    priority="medium",
                ))

            if entry.change_type == "removed":
                recommendations.append(FeedbackRecommendation(
                    category="structure",
                    section=entry.section,
                    description=(
                        "Content was removed. "
                        "Consider whether this section is needed."
                    ),
                    priority="low",
                ))

        return recommendations

    def _ai_analysis(
        self,
        diff: ReportDiff,
    ) -> tuple[str, list[FeedbackRecommendation]]:
        """Use Claude CLI to analyze the diff intelligently."""
        diff_text = "\n\n".join(
            f"[{e.change_type}] Section: {e.section}\n"
            f"Original: {e.original[:500]}\n"
            f"Edited: {e.edited[:500]}"
            for e in diff.entries[:10]
        )

        prompt = FEEDBACK_ANALYSIS_PROMPT.format(
            original_text=diff_text,
            edited_text="(changes shown above)",
        )

        response = self.client.generate(prompt=prompt)  # type: ignore[union-attr]
        try:
            raw_recs = json.loads(response)
            recs = [
                FeedbackRecommendation(
                    category=r.get("category", "general"),
                    section=r.get("section", "unknown"),
                    description=r.get("description", ""),
                    priority=r.get("priority", "medium"),
                )
                for r in raw_recs
            ]
        except (json.JSONDecodeError, TypeError):
            return response, []
        else:
            return response, recs
