"""Verify layout output (Lists, Callouts, Cards, Code, Quotes, Columns)."""

import shutil
from pathlib import Path
from typing import Any

from pygramattic_reports.models import (
    Report,
    ReportSection,
    SectionType,
    ThemeSpec,
)
from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.outputs.markdown_adapter import MarkdownAdapter


def main():
    output_dir = Path("data/verify_layout")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sections = [
        ReportSection(
            section_type=SectionType.HEADING, title="Layout Verification", level=1
        ),
        
        # 1. Lists
        ReportSection(
            section_type=SectionType.LIST,
            title="Feature List",
            list_data=["Item 1", "Item 2", "Item 3"]
        ),
        
        # 2. Callouts
        ReportSection(
            section_type=SectionType.CALLOUT,
            callout_data={"type": "info", "content": "This is an info callout."}
        ),
        ReportSection(
            section_type=SectionType.CALLOUT,
            callout_data={"type": "warning", "content": "Watch out for this warning!"}
        ),
        
        # 3. Metric Cards
        ReportSection(
            section_type=SectionType.METRIC_CARD,
            card_data={"label": "Total Revenue", "value": "$1.2M", "unit": ""}
        ),
        
        # 4. Code Blocks
        ReportSection(
            section_type=SectionType.CODE_BLOCK,
            title="Example Code",
            code_data={"language": "python", "code": "def hello():\n    print('world')"}
        ),
        
        # 5. Quotes
        ReportSection(
            section_type=SectionType.QUOTE,
            quote_data={"text": "The greatest glory in living lies not in never falling, but in rising every time we fall.", "author": "Nelson Mandela"}
        ),
        
        # 6. Columns (Nested)
        ReportSection(
            section_type=SectionType.COLUMNS,
            title="Two Column Layout (Flattened in MD)",
            columns_data=[
                ReportSection(
                    section_type=SectionType.NARRATIVE,
                    title="Column 1",
                    content="Content for column 1."
                ),
                ReportSection(
                    section_type=SectionType.NARRATIVE,
                    title="Column 2",
                    content="Content for column 2."
                ),
            ]
        ),
    ]
    
    report = Report(
        id=generate_id(),
        name="Layout Report",
        sections=sections,
        template_name="layout_test",
        theme_name="default",
        build_timestamp=now_utc(),
    )
    
    # Render
    adapter = MarkdownAdapter(media_dir=output_dir / "media")
    md_output = adapter.render(report, ThemeSpec(name="default"))
    
    # Save
    output_file = output_dir / "layout_report.md"
    output_file.write_bytes(md_output)
    
    print(f"Generated Layout report at: {output_file.absolute()}")
    print("-" * 40)
    print(md_output.decode("utf-8"))

if __name__ == "__main__":
    main()
