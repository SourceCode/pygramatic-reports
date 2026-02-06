"""Feedback tool for improving report quality.

Compare original and edited reports, analyze changes, and
produce actionable recommendations.

Usage::

    from pygramattic_reports.feedback import ReportDiffer, FeedbackAnalyzer

    differ = ReportDiffer()
    diff = differ.compare(original_path, edited_path)

    analyzer = FeedbackAnalyzer(claude_client)
    feedback = analyzer.analyze(diff)
"""

from .analyzer import FeedbackAnalyzer, FeedbackRecommendation, FeedbackReport
from .differ import DiffEntry, ReportDiff, ReportDiffer

__all__ = [
    "DiffEntry",
    "FeedbackAnalyzer",
    "FeedbackRecommendation",
    "FeedbackReport",
    "ReportDiff",
    "ReportDiffer",
]
