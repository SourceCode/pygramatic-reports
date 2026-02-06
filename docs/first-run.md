# First Run Guide

This guide will walk you through generating your first report using Pygramattic Reports.

## 1. Initialize Project

Navigate to your workspace and initialize a new report project:

```bash
mkdir my-first-report
cd my-first-report
report init
```

This will create the necessary directory structure (`data/`, `config/`) and a default `config.yaml`.

## 2. Prepare Data

Place a sample CSV file in `data/raw/`. For this example, let's create a simple sales file:

```bash
echo "date,product,amount\n2023-01-01,Widget A,100\n2023-01-02,Widget B,150" > data/raw/sales.csv
```

## 3. Configure Report

Edit `config.yaml` to point to your data:

```yaml
inputs:
  - type: "csv"
    path: "data/raw/sales.csv"
    name: "sales_data"

template: "standard_report"
```

## 4. Ingest Data

Run the ingestion command to normalize your data:

```bash
report ingest data/raw/sales.csv
```

You should see output confirming the file was processed and saved to `data/processed/`.

## 5. Build Report

Generate the final report:

```bash
report build --config config.yaml
```

The report will be generated in `data/reports/` (e.g., `data/reports/report_2023-10-27.md`).

## 6. Verify Output

Open the generated report to verify the contents:

```bash
cat data/reports/*.md
```

## Next Steps

*   Explore [Functionality](/docs/functionality.md) to learn about advanced features.
*   Check [Integrations](/docs/integrations.md) to connect Google Drive.
