# First Run Guide

This guide walks you through the "Golden Path" of generating your first report from scratch.

## 1. Initialize Project

Create a standardized directory structure for your reporting project.

```bash
mkdir my-reports
cd my-reports
report init .
```

This creates:
*   `config.yaml` (default configuration)
*   `data/` (folder for inputs)
*   `templates/` (sample templates)
*   `themes/` (sample themes)

## 2. Ingest Data

Place a sample CSV file in the data directory.

```bash
# Create dummy data
echo "product,amount,date
Widget A,100,2023-01-01
Widget B,200,2023-01-02" > data/sample.csv
```

## 3. Configure the Job

Edit `config.yaml` to point to your new data:

```yaml
template: "default_summary"
theme: "default"
datasets:
  main: "data/sample.csv"
```

## 4. Build Report

Run the build command:

```bash
report build --config config.yaml
```

**Output**:
*   `output/report.html`: The rendered HTML report.
*   `output/report.pdf`: (If enabled) PDF version.

## 5. View Result

Open the generated HTML file in your browser:

```bash
# macOS
open output/report.html

# Linux
xdg-open output/report.html

# Windows
start output/report.html
```

## Next Steps

*   Learn about **[Templates](/docs/functionality.md)** to customize the layout.
*   Explore **[Themes](/docs/functionality.md)** to change the styling.
*   See **[API Reference](/docs/api.md)** for programmatic generation.
