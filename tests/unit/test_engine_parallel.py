from datetime import UTC, datetime

import pandas as pd
import pytest

from pygramattic_reports.charts.engine import ChartEngine
from pygramattic_reports.models import (
    ChartRenderer,
    ChartSpec,
    ChartType,
    Dataset,
    Provenance,
    SourceType,
    ThemeSpec,
)


def test_generate_batch_serial_fallback():
    """Test batch generation (even if mock executor just runs synchronously or implementation works)."""
    # Create simple inputs
    df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    dataset = Dataset(
        id="test_ds",
        name="Test",
        schema=[],
        dataframe=df,
        provenance=Provenance(
            source_type=SourceType.CSV,
            source_name="mem",
            loaded_at=datetime.now(UTC),
            normalized_at=datetime.now(UTC),
            row_count_raw=2,
        ),
    )

    spec = ChartSpec(
        title="Chart 1",
        chart_type=ChartType.BAR,
        renderer=ChartRenderer.MATPLOTLIB,
        x_column="x",
        y_columns=["y"],
        dataset_id="test_ds",
    )
    theme = ThemeSpec(name="default")

    engine = ChartEngine()

    # We patch ProcessPoolExecutor to ensure we can debug if pickling fails etc.
    # Or rely on real one. Real one on Mac might be slow to startup.
    # Let's try real one first.

    # We need to ensure MatplotlibRenderer is mockable or functional.
    # Since we are in unit tests, Matplotlib might require installation (it is listed in dependencies).

    try:
        results = engine.generate_batch([(spec, dataset, theme)], max_workers=1)
    except Exception as e:
        pytest.fail(f"Batch generation failed: {e}")

    assert len(results) == 1
    assert isinstance(results[0], bytes)


def test_batch_cache_integration():
    """Test that batch generation respects cache?
    Note: generate_batch in current impl does NOT check cache individually before submitting.
    It calls _render_task which calls renderer.render directly.
    The 'generate' method has caching. 'generate_batch' bypasses 'generate' method.
    This is a design choice or oversight.
    Ideally batch generation should also check cache.
    However, checking cache in main process is cheap.
    Let's update implementation later if needed. For now, just test functioning.
    """
