# Functionality & Workflows

Pygramattic Reports allows you to automate the lifecycle of report generation from data ingestion to final validation.

## Core Workflows

### 1. Ingestion Pipeline
The ingestion pipeline is responsible for bringing data into the system.
*   **Discovery**: Identifies files in `data/raw` or connects to external APIs.
*   **Validation**: Checks file integrity and format.
*   **Normalization**: Converts specific formats (e.g., CSV, Google Sheet) into the internal Schema.

### 2. Processing Engine
Once data is normalized, the processing engine applies transformations:
*   **Cleaning**: Handling missing values, type casting.
*   **Aggregation**: Grouping, summing, averaging (Pandas-based).
*   **Derivation**: creating new metrics from existing data.

### 3. Report Builder
The builder merges processed data with templates:
*   **Templating**: Uses Jinja2 to render text and structure.
*   **Charting**: Generates static assets (PNG/SVG) for embedding.
*   **Assembly**: Produces the final artifact (Markdown, DOCX).

### 4. Continuous Feedback
*   **Diff Analysis**: Compares generated reports with human-edited versions.
*   **Optimization**: Adjusts specific template parameters or prompt logic based on diffs.

## Key Features

### Template System
Templates define the *structure* of a report. They support:
*   Variables (`{{ sales.total }}`)
*   Loops (`{% for item in items %}`)
*   Conditionals (`{% if profit > 0 %}`)
*   Chart placeholders (`{{ chart('sales_trend') }}`)

### Theme System
Themes define the *style* of a report. They control:
*   Color palettes (for charts and text)
*   Font families and sizes
*   Spacing and layout constraints

### Multi-Format Output
Generate the same report in multiple formats without changing the core logic:
*   **Markdown**: For technical documentation and wikis.
*   **DOCX**: For business stakeholders.
*   **JSON**: For machine-to-machine integration.
