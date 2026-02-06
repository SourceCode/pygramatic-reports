"""Verify document structure output (Frontmatter, CoverPage, TOC)."""

import shutil
from datetime import datetime
from pathlib import Path

from pygramattic_reports.models import (
    CoverPageSpec,
    DocumentMetadata,
    PageLayout,
    Report,
    ReportSection,
    SectionType,
    ThemeSpec,
)
from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.outputs.markdown_adapter import MarkdownAdapter


def main():
    output_dir = Path("data/verify_docs")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create Report with new Metadata/Structure
    metadata = DocumentMetadata(
        title="Q1 Financial Report",
        author="Finance Team",
        version="v1.0",
        keywords=["finance", "quarterly", "2024"],
        created_at=now_utc(),
    )
    
    cover_page = CoverPageSpec(
        title="Quarterly Financial Results",
        subtitle="Q1 2024 Performance Review",
        logo_path="logo.png",
    )
    
    sections = [
        ReportSection(
            section_type=SectionType.COVER_PAGE,
            metadata={"spec": cover_page.model_dump()}
        ),
        ReportSection(
            section_type=SectionType.TABLE_OF_CONTENTS,
            title="Contents"
        ),
        ReportSection(
            section_type=SectionType.HEADING,
            title="Executive Summary",
            level=1
        ),
        ReportSection(
            section_type=SectionType.NARRATIVE,
            content="This has been a strong quarter."
        ),
        ReportSection(
            section_type=SectionType.HEADING,
            title="Financial Performance",
            level=1
        ),
         ReportSection(
            section_type=SectionType.HEADING,
            title="Revenue",
            level=2
        ),
        ReportSection(
            section_type=SectionType.NARRATIVE,
            content="Revenue is up 10%."
        ),
    ]
    
    report = Report(
        id=generate_id(),
        name="Q1 Report",
        sections=sections,
        template_name="financial",
        theme_name="corporate",
        build_timestamp=now_utc(),
        metadata=metadata,
        cover_page=cover_page,
    )
    
    # 2. Render to Markdown
    adapter = MarkdownAdapter(media_dir=output_dir / "media")
    md_output = adapter.render(report, ThemeSpec(name="default"))
    
    # 3. Save
    output_file = output_dir / "report.md"
    output_file.write_bytes(md_output)
    
    print(f"Generated Markdown report at: {output_file.absolute()}")
    print("-" * 40)
    print(md_output.decode("utf-8")[:500] + "...") # Print visual preview

if __name__ == "__main__":
    main()
