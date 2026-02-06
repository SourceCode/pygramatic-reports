"""Verify Theme System HTML output."""

import shutil
from pathlib import Path

from pygramattic_reports.models import (
    ReportSection,
    SectionType,
    ThemeSpec,
    Report,
    ColorSpec,
    FontSpec,
)
from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.outputs.html_adapter import HtmlAdapter


def main():
    output_dir = Path("data/verify_theme")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Define a Custom Theme
    custom_theme = ThemeSpec(
        name="cyberpunk",
        colors=ColorSpec(
            primary="#00ff00",
            secondary="#ff00ff",
            accent="#00ffff",
            background="#000000",
            text="#ffffff",
            text_light="#cccccc",
            chart_palette=["#ff00ff", "#00ffff", "#00ff00"]
        ),
        fonts=FontSpec(
            heading="Courier New",
            body="Arial",
            monospace="Consolas"
        )
    )

    # 2. Define Content
    sections = [
        ReportSection(section_type=SectionType.TITLE, content="Cyberpunk Report"),
        
        ReportSection(
            section_type=SectionType.NARRATIVE,
            title="Introduction",
            content="This report demonstrates the vivid Cyberpunk theme applied automatically via CSS variables."
        ),
        
        ReportSection(
            section_type=SectionType.METRIC_CARD,
            card_data={"label": "System Status", "value": "ONLINE"}
        ),
        
        ReportSection(
            section_type=SectionType.CALLOUT,
            callout_data={"type": "warning", "content": "Rogue AI detected in sector 7."}
        ),
        
        ReportSection(
            section_type=SectionType.LIST,
            title="Active Protocols",
            list_data=["Protocol Omega", "Protocol Alpha", "Protocol Zed"]
        ),
        
        ReportSection(
            section_type=SectionType.CODE_BLOCK,
            title="Override Code",
            code_data={"language": "bash", "code": "sudo rm -rf /virus"}
        )
    ]
    
    report = Report(
        id=generate_id(),
        name="Theme Verification",
        sections=sections,
        template_name="test",
        theme_name="cyberpunk",
        build_timestamp=now_utc(),
    )
    
    # render
    adapter = HtmlAdapter()
    html_bytes = adapter.render(report, custom_theme)
    
    out_file = output_dir / "cyberpunk_report.html"
    out_file.write_bytes(html_bytes)
    
    print(f"Generated themed report: {out_file.absolute()}")

if __name__ == "__main__":
    main()
