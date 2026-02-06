"""Basic example of generating a report using the Pygramattic Fluent API."""

from pathlib import Path
import pandas as pd
from pygramattic_reports.api import Pygramattic

def main():
    print("Generating report...")
    
    # 1. Create sample data
    data = [
        {"Quarter": "Q1", "Revenue": 10000, "Cost": 8000},
        {"Quarter": "Q2", "Revenue": 12000, "Cost": 8500},
        {"Quarter": "Q3", "Revenue": 15000, "Cost": 9000},
        {"Quarter": "Q4", "Revenue": 18000, "Cost": 10000},
    ]
    df = pd.DataFrame(data)
    
    # 2. Build Report
    report = (
        Pygramattic()
        .configure(
            title="Annual Financial Summary", 
            author="Pygramattic Demo",
            subject="Financials"
        )
        .add_dataset("financials", df)
        .add_section(
            title="Executive Summary", 
            content="This report summarizes the financial performance for the fiscal year. Revenue showed consistent growth."
        )
        # Add a Bar Chart comparing Revenue
        .add_chart(
            title="Revenue Trend",
            dataset="financials",
            chart_type="bar",
            x_col="Quarter",
            y_cols=["Revenue"],
            description="Quarterly revenue performance."
        )
        # Add a Table
        # Note: API add_section generic can be used, but specialized support is better.
        # For now, we rely on the implementation details or templates.
        # The Fluent API in Phase 7 implementation was basic.
        .build()
    )
    
    # 3. Save
    output_dir = Path("output_examples")
    output_dir.mkdir(exist_ok=True)
    
    print(f"Saving to {output_dir}...")
    report.save(output_dir / "financial_report.html")
    report.save(output_dir / "financial_report.md")
    
    # Optional formats if dependencies installed
    try:
        report.save(output_dir / "financial_report.xlsx")
        print("Saved Excel report.")
    except Exception as e:
        print(f"Skipping Excel: {e}")

    try:
        report.save(output_dir / "financial_report.pptx")
        print("Saved PowerPoint report.")
    except Exception as e:
        print(f"Skipping PPTX: {e}")

    print("Done!")

if __name__ == "__main__":
    main()
