# Phase 20: Feedback Tool & Final CLI Commands

## Objective

Implement the feedback engine that compares original and edited reports to improve future generation, and complete all remaining CLI commands (`report validate`, `report feedback`). This phase finishes the V1 feature set.

## Why This Phase Is Twentieth (Final)

The feedback tool is the last major subsystem in the PRD. It depends on the entire pipeline being functional (reports must be generated, edited by a user, then fed back). The remaining CLI commands (`validate`, `feedback`) wire the last two modules into the user interface.

## Tasks

### Task 20.1: Implement the Report Differ

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/feedback/differ.py`

**Description:** Compares an original report with an edited version and produces a structured diff.

**Requirements:**
- Support comparing Markdown files (text diff)
- Support comparing DOCX files (extract text, then diff)
- Produce a structured diff with: added, removed, and changed sections
- Identify which sections were modified

```python
import difflib
from pathlib import Path
from dataclasses import dataclass
from pygramattic_reports.exceptions import FeedbackError


@dataclass
class DiffEntry:
    """A single difference between original and edited report."""
    section: str          # Section identifier or line range
    change_type: str      # "added", "removed", "modified"
    original: str         # Original text (empty for added)
    edited: str           # Edited text (empty for removed)


@dataclass
class ReportDiff:
    """Structured diff between original and edited report."""
    original_path: str
    edited_path: str
    format: str
    entries: list[DiffEntry]
    total_changes: int
    summary: str          # Human-readable summary of changes


class ReportDiffer:
    """Compares original and edited reports to identify changes.

    Supports Markdown and DOCX comparison. Produces a structured
    diff that the feedback analyzer can use to suggest adjustments.

    Usage:
        differ = ReportDiffer()
        diff = differ.compare(
            original=Path("report_v1.md"),
            edited=Path("report_v1_edited.md"),
        )
    """

    def compare(self, original: Path, edited: Path) -> ReportDiff:
        """Compare two report files.

        Auto-detects format from file extension.

        Args:
            original: Path to the original generated report
            edited: Path to the user-edited version

        Returns:
            Structured diff of changes

        Raises:
            FeedbackError: If files cannot be compared
        """
        if not original.exists():
            raise FeedbackError(f"Original file not found: {original}")
        if not edited.exists():
            raise FeedbackError(f"Edited file not found: {edited}")

        ext = original.suffix.lower()
        if ext == ".md":
            return self._compare_text(original, edited, "markdown")
        elif ext == ".docx":
            return self._compare_docx(original, edited)
        elif ext == ".txt":
            return self._compare_text(original, edited, "text")
        else:
            raise FeedbackError(f"Unsupported format for comparison: {ext}")

    def _compare_text(self, original: Path, edited: Path, format: str) -> ReportDiff:
        """Compare two text-based files."""
        orig_lines = original.read_text(encoding="utf-8").splitlines()
        edit_lines = edited.read_text(encoding="utf-8").splitlines()

        diff = difflib.unified_diff(orig_lines, edit_lines, lineterm="")
        entries = self._parse_unified_diff(list(diff))

        return ReportDiff(
            original_path=str(original),
            edited_path=str(edited),
            format=format,
            entries=entries,
            total_changes=len(entries),
            summary=self._generate_summary(entries),
        )

    def _compare_docx(self, original: Path, edited: Path) -> ReportDiff:
        """Compare two DOCX files by extracting text and diffing."""
        from docx import Document

        orig_doc = Document(str(original))
        edit_doc = Document(str(edited))

        orig_text = [p.text for p in orig_doc.paragraphs if p.text.strip()]
        edit_text = [p.text for p in edit_doc.paragraphs if p.text.strip()]

        diff = difflib.unified_diff(orig_text, edit_text, lineterm="")
        entries = self._parse_unified_diff(list(diff))

        return ReportDiff(
            original_path=str(original),
            edited_path=str(edited),
            format="docx",
            entries=entries,
            total_changes=len(entries),
            summary=self._generate_summary(entries),
        )

    def _parse_unified_diff(self, diff_lines: list[str]) -> list[DiffEntry]:
        """Parse unified diff output into structured DiffEntry objects."""
        ...

    def _generate_summary(self, entries: list[DiffEntry]) -> str:
        """Generate a human-readable summary of changes."""
        added = sum(1 for e in entries if e.change_type == "added")
        removed = sum(1 for e in entries if e.change_type == "removed")
        modified = sum(1 for e in entries if e.change_type == "modified")
        parts = []
        if added: parts.append(f"{added} additions")
        if removed: parts.append(f"{removed} removals")
        if modified: parts.append(f"{modified} modifications")
        return ", ".join(parts) if parts else "No changes detected"
```

---

### Task 20.2: Implement the Feedback Analyzer

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/feedback/analyzer.py`

**Description:** Analyzes diffs using Claude CLI and produces actionable feedback recommendations.

```python
import json
from pygramattic_reports.ai import ClaudeClient
from pygramattic_reports.ai.prompts import FEEDBACK_ANALYSIS_PROMPT
from pygramattic_reports.exceptions import AIError, FeedbackError
from pygramattic_reports.logging import get_logger
from .differ import ReportDiff, DiffEntry

logger = get_logger("feedback")


@dataclass
class FeedbackRecommendation:
    """A single recommendation for improving future reports."""
    category: str          # "conciseness", "accuracy", "tone", "structure", "data_emphasis"
    section: str           # Which section this applies to
    description: str       # What should change
    priority: str          # "high", "medium", "low"


@dataclass
class FeedbackReport:
    """Complete feedback analysis."""
    diff: ReportDiff
    recommendations: list[FeedbackRecommendation]
    ai_analysis: str | None   # Raw AI analysis (if available)


class FeedbackAnalyzer:
    """Analyzes report diffs and produces improvement recommendations.

    For V1, feedback produces recommendations for human review.
    It does NOT automatically modify templates or prompts.

    Usage:
        analyzer = FeedbackAnalyzer(claude_client)
        feedback = analyzer.analyze(diff)
    """

    def __init__(self, client: ClaudeClient | None = None):
        self.client = client

    def analyze(self, diff: ReportDiff) -> FeedbackReport:
        """Analyze a diff and produce recommendations.

        If Claude CLI is available, uses AI for intelligent analysis.
        Otherwise, produces basic rule-based recommendations.
        """
        recommendations = []

        # Rule-based analysis (always runs)
        recommendations.extend(self._basic_analysis(diff))

        # AI analysis (optional)
        ai_analysis = None
        if self.client and self.client.is_available() and diff.entries:
            try:
                ai_analysis, ai_recs = self._ai_analysis(diff)
                recommendations.extend(ai_recs)
            except (AIError, FeedbackError) as e:
                logger.warning("AI feedback analysis failed", error=str(e))

        return FeedbackReport(
            diff=diff,
            recommendations=recommendations,
            ai_analysis=ai_analysis,
        )

    def _basic_analysis(self, diff: ReportDiff) -> list[FeedbackRecommendation]:
        """Rule-based analysis of common feedback patterns."""
        recommendations = []

        for entry in diff.entries:
            # Pattern: text was shortened → recommend conciseness
            if entry.change_type == "modified" and len(entry.edited) < len(entry.original) * 0.7:
                recommendations.append(FeedbackRecommendation(
                    category="conciseness",
                    section=entry.section,
                    description="Content was shortened significantly. Consider reducing verbosity in future generation.",
                    priority="medium",
                ))

            # Pattern: text was expanded → may need more detail
            if entry.change_type == "modified" and len(entry.edited) > len(entry.original) * 1.5:
                recommendations.append(FeedbackRecommendation(
                    category="detail",
                    section=entry.section,
                    description="Content was expanded. Consider adding more detail in future generation.",
                    priority="medium",
                ))

            # Pattern: content was removed → may be unnecessary
            if entry.change_type == "removed":
                recommendations.append(FeedbackRecommendation(
                    category="structure",
                    section=entry.section,
                    description="Content was removed. Consider whether this section is needed.",
                    priority="low",
                ))

        return recommendations

    def _ai_analysis(self, diff: ReportDiff) -> tuple[str, list[FeedbackRecommendation]]:
        """Use Claude CLI to analyze the diff intelligently."""
        # Format the diff for the prompt
        diff_text = "\n\n".join(
            f"[{e.change_type}] Section: {e.section}\n"
            f"Original: {e.original[:500]}\n"
            f"Edited: {e.edited[:500]}"
            for e in diff.entries[:10]  # Limit to 10 entries
        )

        prompt = FEEDBACK_ANALYSIS_PROMPT.format(
            original_text=diff_text,
            edited_text="(changes shown above)",
        )

        response = self.client.generate(prompt=prompt)
        # Parse response as JSON array of recommendations
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
            return response, recs
        except (json.JSONDecodeError, TypeError):
            # AI response wasn't valid JSON -- return raw text
            return response, []
```

---

### Task 20.3: Create Feedback Package Init

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/feedback/__init__.py`

```python
"""Feedback tool for improving report quality.

Compare original and edited reports, analyze changes, produce recommendations.

Usage:
    from pygramattic_reports.feedback import ReportDiffer, FeedbackAnalyzer

    differ = ReportDiffer()
    diff = differ.compare(original_path, edited_path)

    analyzer = FeedbackAnalyzer(claude_client)
    feedback = analyzer.analyze(diff)
"""
from .differ import ReportDiffer, ReportDiff, DiffEntry
from .analyzer import FeedbackAnalyzer, FeedbackReport, FeedbackRecommendation

__all__ = [
    "ReportDiffer", "ReportDiff", "DiffEntry",
    "FeedbackAnalyzer", "FeedbackReport", "FeedbackRecommendation",
]
```

---

### Task 20.4: Implement the `validate` CLI Command

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/cli/validate_cmd.py`

**Interface:**
```
report validate <report_path> [OPTIONS]

Arguments:
  report_path    Path to the generated report file, OR a report ID from storage

Options:
  --dataset-dir    Directory containing source datasets (auto-detected from build log if available)
  --strict         Fail on warnings (default: only fail on errors)
  --no-ai          Skip AI-assisted narrative validation
  --output, -o     Save validation report to file (JSON)
```

**Example output:**
```
$ report validate data/reports/abc12345/report.md

Validating: data/reports/abc12345/report.md
  Template: quarterly_report
  Datasets: main_data (150 rows)

Structural checks:
  ✓ Section count: 7/7
  ✓ Data tables: 2/2 have content
  ✓ Charts: 2/2 have images

Numerical checks:
  ✓ 45 values verified against source data
  ✗ revenue total: expected 8340.50, got 8341.00 (section 3)

Narrative checks:
  ⊘ Skipped (AI unavailable)

Result: WARN (44 passed, 1 failed, 0 warnings)
```

---

### Task 20.5: Implement the `feedback` CLI Command

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/cli/feedback_cmd.py`

**Interface:**
```
report feedback <original> <edited> [OPTIONS]

Arguments:
  original    Path to the original generated report
  edited      Path to the user-edited version

Options:
  --output, -o    Save feedback report to file (JSON)
  --format        Report format for comparison (auto-detected from extension)
```

**Example output:**
```
$ report feedback report_v1.md report_v1_edited.md

Comparing: report_v1.md → report_v1_edited.md
  Format: markdown
  Changes: 3 modifications, 1 removal

Recommendations:
  1. [Conciseness] Executive Summary: Content was shortened by 40%.
     → Consider reducing verbosity in future generation.

  2. [Structure] Appendix section: Was removed entirely.
     → Consider whether this section is needed in the template.

  3. [Detail] Detailed Analysis: Content was expanded significantly.
     → Consider adding more specific data points in future AI prompts.

Feedback saved to: data/feedback/report_v1_feedback.json
```

---

### Task 20.6: Wire Final CLI Commands

**File to update:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/cli/main.py`

Add all remaining commands:
```python
from .validate_cmd import validate
from .feedback_cmd import feedback

app.command()(validate)
app.command()(feedback)
```

**Final CLI command listing:**
```
report --help

Commands:
  ingest    Ingest a data file into the storage system
  build     Build a report from a configuration file
  validate  Validate a generated report against source data
  feedback  Analyze changes between original and edited reports
  export    Export a dataset to a different format
  list      List datasets, reports, templates, or themes
  init      Scaffold a new report configuration file
```

---

### Task 20.7: Write Feedback and Validation CLI Tests

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_feedback.py`

**Test cases:**
1. `test_differ_markdown` -- Compare two markdown files, produce diff
2. `test_differ_no_changes` -- Same file produces empty diff
3. `test_differ_file_not_found` -- Missing file raises FeedbackError
4. `test_basic_analysis_conciseness` -- Shortened text triggers conciseness recommendation
5. `test_basic_analysis_expansion` -- Expanded text triggers detail recommendation
6. `test_basic_analysis_removal` -- Removed text triggers structure recommendation
7. `test_ai_analysis_mocked` -- AI analysis produces recommendations (mocked)
8. `test_ai_analysis_unavailable` -- Graceful fallback when AI unavailable

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/integration/test_validate_feedback.py`

**Integration test cases:**
1. `test_validate_built_report` -- Build a report then validate it, expect PASS
2. `test_validate_prints_results` -- CLI prints validation results
3. `test_feedback_produces_recommendations` -- Full feedback workflow

---

### Task 20.8: Write End-to-End Integration Test

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/integration/test_e2e.py`

**Description:** The ultimate integration test: exercises the entire pipeline from raw data to validated report.

```python
def test_full_pipeline_csv_to_validated_report(tmp_path):
    """
    Complete end-to-end test:
    1. Ingest a CSV file
    2. Build a report (Markdown + DOCX, no AI)
    3. Validate the report
    4. Verify all outputs exist and are valid
    """
    # 1. Create test data
    csv_content = "region,revenue,quarter\nUS,1500,Q1\nEU,2300,Q1\nAPAC,890,Q1\n"
    csv_path = tmp_path / "input.csv"
    csv_path.write_text(csv_content)

    # 2. Ingest
    # ... invoke ingest command ...

    # 3. Build
    # ... invoke build command ...

    # 4. Validate
    # ... invoke validate command ...

    # 5. Assert
    # - Markdown file exists and contains expected sections
    # - DOCX file exists and is valid
    # - Build log exists
    # - Validation result is PASS or WARN (not FAIL)
```

---

## Dependencies

- **Depends on:** Phase 13 (Builder), Phase 17 (Claude client), Phase 19 (Validator)
- **Blocks:** Nothing (this is the final V1 phase)

## Acceptance Criteria

1. `ReportDiffer` produces structured diffs for Markdown and DOCX files
2. `FeedbackAnalyzer` generates actionable recommendations
3. `report validate` runs all three validation layers and prints results
4. `report feedback` compares reports and produces recommendations
5. All CLI commands are registered and documented
6. End-to-end integration test passes
7. All tests pass

## References

- PRD Feedback Tool: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 179-193)
- PRD Feedback Engine Module: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 359-364)
- PRD CLI validate/feedback commands: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 379-380)
- PRD Validator: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 147-158)
