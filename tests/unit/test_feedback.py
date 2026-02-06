"""Tests for feedback differ and analyzer (Phase 20)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from pygramattic_reports.exceptions import AIError, FeedbackError
from pygramattic_reports.feedback import (
    FeedbackAnalyzer,
    ReportDiffer,
)
from pygramattic_reports.feedback.differ import DiffEntry, ReportDiff

if TYPE_CHECKING:
    from pathlib import Path

import pytest

# ---------- Differ: markdown comparison --------------------------------------


class TestDifferMarkdown:
    """Compare two markdown files, produce diff."""

    def test_differ_detects_changes(self, tmp_path: Path) -> None:
        orig = tmp_path / "report.md"
        edited = tmp_path / "report_edited.md"
        orig.write_text("# Title\n\nOriginal content here.\n")
        edited.write_text("# Title\n\nEdited content here.\n")

        diff = ReportDiffer().compare(orig, edited)

        assert diff.format == "markdown"
        assert diff.total_changes >= 1
        assert any(e.change_type == "modified" for e in diff.entries)

    def test_differ_detects_additions(self, tmp_path: Path) -> None:
        orig = tmp_path / "report.md"
        edited = tmp_path / "report_edited.md"
        orig.write_text("# Title\n")
        edited.write_text("# Title\n\nNew paragraph added.\n")

        diff = ReportDiffer().compare(orig, edited)

        assert diff.total_changes >= 1
        assert any(e.change_type == "added" for e in diff.entries)

    def test_differ_detects_removals(self, tmp_path: Path) -> None:
        orig = tmp_path / "report.md"
        edited = tmp_path / "report_edited.md"
        orig.write_text("# Title\n\nParagraph to remove.\n")
        edited.write_text("# Title\n")

        diff = ReportDiffer().compare(orig, edited)

        assert diff.total_changes >= 1
        assert any(e.change_type == "removed" for e in diff.entries)


# ---------- Differ: no changes -----------------------------------------------


class TestDifferNoChanges:
    """Same file produces empty diff."""

    def test_identical_files_no_changes(self, tmp_path: Path) -> None:
        orig = tmp_path / "report.md"
        edited = tmp_path / "same.md"
        content = "# Title\n\nSame content.\n"
        orig.write_text(content)
        edited.write_text(content)

        diff = ReportDiffer().compare(orig, edited)

        assert diff.total_changes == 0
        assert diff.summary == "No changes detected"


# ---------- Differ: file not found -------------------------------------------


class TestDifferFileNotFound:
    """Missing file raises FeedbackError."""

    def test_missing_original(self, tmp_path: Path) -> None:
        edited = tmp_path / "edited.md"
        edited.write_text("content")
        with pytest.raises(FeedbackError, match="not found"):
            ReportDiffer().compare(tmp_path / "missing.md", edited)

    def test_missing_edited(self, tmp_path: Path) -> None:
        orig = tmp_path / "original.md"
        orig.write_text("content")
        with pytest.raises(FeedbackError, match="not found"):
            ReportDiffer().compare(orig, tmp_path / "missing.md")

    def test_unsupported_format(self, tmp_path: Path) -> None:
        orig = tmp_path / "report.pdf"
        edited = tmp_path / "edited.pdf"
        orig.write_text("content")
        edited.write_text("content")
        with pytest.raises(FeedbackError, match="Unsupported"):
            ReportDiffer().compare(orig, edited)


# ---------- Analyzer: conciseness --------------------------------------------


class TestBasicAnalysisConciseness:
    """Shortened text triggers conciseness recommendation."""

    def test_conciseness_recommendation(self) -> None:
        diff = ReportDiff(
            original_path="a.md",
            edited_path="b.md",
            format="markdown",
            entries=[
                DiffEntry(
                    section="@@ line 1",
                    change_type="modified",
                    original="A" * 100,
                    edited="A" * 30,
                ),
            ],
            total_changes=1,
            summary="1 modifications",
        )

        report = FeedbackAnalyzer().analyze(diff)

        assert any(r.category == "conciseness" for r in report.recommendations)


# ---------- Analyzer: expansion ----------------------------------------------


class TestBasicAnalysisExpansion:
    """Expanded text triggers detail recommendation."""

    def test_expansion_recommendation(self) -> None:
        diff = ReportDiff(
            original_path="a.md",
            edited_path="b.md",
            format="markdown",
            entries=[
                DiffEntry(
                    section="@@ line 1",
                    change_type="modified",
                    original="A" * 50,
                    edited="A" * 100,
                ),
            ],
            total_changes=1,
            summary="1 modifications",
        )

        report = FeedbackAnalyzer().analyze(diff)

        assert any(r.category == "detail" for r in report.recommendations)


# ---------- Analyzer: removal ------------------------------------------------


class TestBasicAnalysisRemoval:
    """Removed text triggers structure recommendation."""

    def test_removal_recommendation(self) -> None:
        diff = ReportDiff(
            original_path="a.md",
            edited_path="b.md",
            format="markdown",
            entries=[
                DiffEntry(
                    section="@@ line 1",
                    change_type="removed",
                    original="Removed content",
                    edited="",
                ),
            ],
            total_changes=1,
            summary="1 removals",
        )

        report = FeedbackAnalyzer().analyze(diff)

        assert any(r.category == "structure" for r in report.recommendations)


# ---------- Analyzer: AI analysis (mocked) -----------------------------------


class TestAiAnalysisMocked:
    """AI analysis produces recommendations (mocked)."""

    def test_ai_recommendations(self) -> None:
        client = MagicMock()
        client.is_available.return_value = True
        client.generate.return_value = json.dumps([
            {
                "category": "tone",
                "section": "summary",
                "description": "Use more formal language",
                "priority": "high",
            },
        ])

        diff = ReportDiff(
            original_path="a.md",
            edited_path="b.md",
            format="markdown",
            entries=[
                DiffEntry(
                    section="summary",
                    change_type="modified",
                    original="Old text",
                    edited="New text",
                ),
            ],
            total_changes=1,
            summary="1 modifications",
        )

        report = FeedbackAnalyzer(client=client).analyze(diff)

        assert report.ai_analysis is not None
        assert any(r.category == "tone" for r in report.recommendations)
        client.generate.assert_called_once()


# ---------- Analyzer: AI unavailable -----------------------------------------


class TestAiAnalysisUnavailable:
    """Graceful fallback when AI unavailable."""

    def test_no_client(self) -> None:
        diff = ReportDiff(
            original_path="a.md",
            edited_path="b.md",
            format="markdown",
            entries=[
                DiffEntry(
                    section="s1",
                    change_type="removed",
                    original="text",
                    edited="",
                ),
            ],
            total_changes=1,
            summary="1 removals",
        )

        report = FeedbackAnalyzer(client=None).analyze(diff)

        assert report.ai_analysis is None
        assert any(r.category == "structure" for r in report.recommendations)

    def test_ai_failure_graceful(self) -> None:
        client = MagicMock()
        client.is_available.return_value = True
        client.generate.side_effect = AIError("timeout")

        diff = ReportDiff(
            original_path="a.md",
            edited_path="b.md",
            format="markdown",
            entries=[
                DiffEntry(
                    section="s1",
                    change_type="modified",
                    original="A" * 100,
                    edited="A" * 30,
                ),
            ],
            total_changes=1,
            summary="1 modifications",
        )

        report = FeedbackAnalyzer(client=client).analyze(diff)

        assert report.ai_analysis is None
        assert any(r.category == "conciseness" for r in report.recommendations)
