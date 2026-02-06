# API Reference

## CLI Reference

The primary interface for Pygramattic Reports is the `report` command.

### `report init`
Initializes a new project directory.
*   `--path`: Custom path (default: current directory).

### `report ingest`
Ingests a file into the system.
*   `FILES`: List of file paths to ingest.
*   `--type`: Force a specific loader (e.g., `csv`, `json`).
*   `--dry-run`: Validate without saving.

### `report build`
Generates a report.
*   `--config`: Path to YAML config file.
*   `--format`: Override output format (default: uses config).
*   `--output-dir`: Custom output location.

### `report validate`
Verify a generated report.
*   `REPORT_PATH`: Path to the report file.
*   `--strict`: Fail on minor discrepancies.

## Python API

You can use Pygramattic Reports as a library in your own Python scripts.

### Loading Data
```python
from pygramattic_reports.loaders import CsvLoader
from pygramattic_reports.models import RawData

loader = CsvLoader()
raw_data: RawData = loader.load("data/sales.csv")
```

### Normalizing Data
```python
from pygramattic_reports.normalizers import StandardNormalizer

normalizer = StandardNormalizer()
dataset = normalizer.normalize(raw_data)
```

### Generating Charts
```python
from pygramattic_reports.charts import ChartEngine, ChartSpec

engine = ChartEngine()
spec = ChartSpec(type="bar", data=dataset, x="product", y="amount")
image_path = engine.render(spec)
```
