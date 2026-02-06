# Functionality & Features

Pygramattic Reports is designed as a modular pipeline for declarative reporting.

## Core Modules

### 1. Ingestion & Loading
*   **Universal Loaders**: Detects file types (csv, json, xlsx, docx) automatically.
*   **Normalization**: Converts specific formats into a standardized `Dataset` object (Wrapper around Pandas DataFrame + Schema Metadata).
*   **Lazy Loading**: Datasets are streamed or loaded only when accessed.

### 2. Templating Engine
The system uses a declarative YAML-based templating system.

*   **Sections**: Reports are built from blocks (`narrative`, `chart`, `data_table`, `columns`).
*   **Inheritance**: Templates can extend other templates using `extends: parent_template`.
*   **Logic**: Jinja2 expressions `{{ }}` and control structures `{% if %}` are supported within content fields.

### 3. Theme System
Styling is separated from content via Theme files (`.yaml`).

*   **Palettes**: Define semantic colors (primary, secondary, success, error).
*   **Typography**: Font families and sizes for headings, body, and code.
*   **Components**: Controls styling for specific elements like callouts, tables, and charts.

### 4. Data Processing
In-memory transformation pipeline defined in the template:

*   **Filtering**: `filters: [{col: "status", op: "eq", val: "active"}]`
*   **sorting**: `sort: ["-date", "amount"]`
*   **Aggregation**: `group_by: ["region"], aggregations: {amount: "sum"}`
*   **Joins**: Left/Right/Inner/Outer joins between loaded datasets.
*   **Validation**: Validation rules (`completeness`, `range`, `unique`) that trigger warnings or errors.

### 5. AI Integration
(Optional) Integrates with LLMs to generate content:

*   **Summarization**: "Summarize this dataset focusing on sales trends."
*   **Insight Detection**: Identifying anomalies or key drivers in data.
*   **Narrative Generation**: Writing text segments based on data context.

## Core Workflows

### The "Build" Workflow
1.  **Parse Config**: Load job configuration.
2.  **Load Assets**: Read Template and Theme files.
3.  **Resolve Data**: specialized loaders fetch data from disk or APIs.
4.  **Process Template**:
    *   Iterate through sections.
    *   Apply data transforms (filters/joins) for data-driven sections.
    *   Render charts (Matplotlib/Seaborn).
    *   Solve Jinja2 limits.
5.  **Render Output**: Using `OutputAdapters` (HTML, PDF, etc.) to serialize the internal `Report` object.

### The "Inspect" Workflow
Developers can inspect intermediate states:

*   `report inspect manifest`: List all registered datasets.
*   `report inspect schema <id>`: View strict schema of a dataset.
