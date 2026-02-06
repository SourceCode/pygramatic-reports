"""Script to generate sample charts for visual verification."""

import os
from pathlib import Path

import pandas as pd
from pygramattic_reports.charts import ChartEngine
from pygramattic_reports.models import (
    AxisSpec,
    ChartSpec,
    ChartType,
    ColumnSchema,
    Dataset,
    DataType,
    LegendSpec,
    Provenance,
    ThemeSpec,
)
from pygramattic_reports.models.base import generate_id, now_utc


def _make_dataset(data: dict, name: str) -> Dataset:
    df = pd.DataFrame(data)
    # Infer schema roughly
    schema = []
    for col in df.columns:
        dtype = DataType.STRING
        if pd.api.types.is_integer_dtype(df[col]):
            dtype = DataType.INTEGER
        elif pd.api.types.is_float_dtype(df[col]):
            dtype = DataType.FLOAT
        schema.append(ColumnSchema(name=col, dtype=dtype))
        
    return Dataset(
        id=generate_id(),
        name=name,
        schema=schema,
        dataframe=df,
        provenance=Provenance(source_type="verify", source_name="script", loaded_at=now_utc(), normalized_at=now_utc(), row_count_raw=len(df)),
    )

def main():
    output_dir = Path("data/verify_charts")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    engine = ChartEngine()
    theme = ThemeSpec(name="verify")
    
    # 1. Waterfall
    ds_waterfall = _make_dataset(
        {"category": ["Start", "Sales", "Cost", "Tax", "Net"], "value": [0, 1000, -300, -100, 600]},
        "waterfall_data"
    )
    spec_waterfall = ChartSpec(
        chart_type=ChartType.WATERFALL,
        title="Waterfall Chart - Profit & Loss",
        x_column="category",
        y_columns=["value"],
        dataset_id=ds_waterfall.id,
        y_axis=AxisSpec(title="Amount ($)"),
    )
    with open(output_dir / "waterfall.png", "wb") as f:
        f.write(engine.generate(spec_waterfall, ds_waterfall, theme))
        
    # 2. Funnel
    ds_funnel = _make_dataset(
        {"stage": ["Leads", "Qualified", "Proposal", "Closed"], "count": [1000, 400, 150, 50]},
        "funnel_data"
    )
    spec_funnel = ChartSpec(
        chart_type=ChartType.FUNNEL,
        title="Sales Funnel",
        x_column="stage",
        y_columns=["count"],
        dataset_id=ds_funnel.id,
    )
    with open(output_dir / "funnel.png", "wb") as f:
        f.write(engine.generate(spec_funnel, ds_funnel, theme))
        
    # 3. Radar
    ds_radar = _make_dataset(
        {"metric": ["Speed", "Power", "Durability", "Range", "Cost"], "model_a": [80, 90, 70, 60, 40], "model_b": [60, 70, 90, 80, 50]},
        "radar_data"
    )
    spec_radar = ChartSpec(
        chart_type=ChartType.RADAR,
        title="Product Comparison",
        x_column="metric",
        y_columns=["model_a", "model_b"],
        dataset_id=ds_radar.id,
        legend_spec=LegendSpec(position="upper right"),
    )
    with open(output_dir / "radar.png", "wb") as f:
        f.write(engine.generate(spec_radar, ds_radar, theme))
        
    # 4. Gauge
    ds_gauge = _make_dataset(
        {"metric": ["Score"], "value": [75], "max": [100]},
        "gauge_data"
    )
    spec_gauge = ChartSpec(
        chart_type=ChartType.GAUGE,
        title="Performance Score",
        x_column="metric",
        y_columns=["value"],
        dataset_id=ds_gauge.id,
        y_axis=AxisSpec(max_value=100),
    )
    with open(output_dir / "gauge.png", "wb") as f:
        f.write(engine.generate(spec_gauge, ds_gauge, theme))
        
    print(f"Generated verify charts in {output_dir.absolute()}")

if __name__ == "__main__":
    main()
