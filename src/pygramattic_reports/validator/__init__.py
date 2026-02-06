"""Report validation for pygramattic-reports.

Three-layer validation: structural, numerical, and AI-assisted
narrative checking.

Usage::

    from pygramattic_reports.validator import ReportValidator

    validator = ReportValidator(claude_client=client)
    result = validator.validate(report, template, datasets)
"""

from .validator import ReportValidator

__all__ = ["ReportValidator"]
