# Architecture & Implementation

## Repository Layout

```text
src/pygramattic_reports/
├── api.py              # Fluent API entry point
├── builder/            # Orchestrates Report assembly
├── charys/             # Visualization engines (Matplotlib/Seaborn)
├── cli/                # Typer CLI commands
├── config/             # Pydantic settings management
├── core/               # Shared logic (Lazy Loading, Caching)
├── loaders/            # File I/O adapters
├── models/             # Pydantic data models (Schema)
├── outputs/            # Renderers (HTML, PDF, etc.)
├── processors/         # Data transformation logic
├── templates/          # Jinja2 loader & renderer
└── themes/             # Style management
```

## Key Subsystems

### 1. The Builder Pattern
The `ReportBuilder` class is the heart of the system. It:
1.  Resolves the `TemplateSpec`.
2.  Iterates `template.sections`.
3.  Dispatches each to a specific `SectionProcessor`.
4.  Accumulates results in a `Report` object.

This separation allows for a multi-pass architecture where we can validate claims (numbers) against the source data *after* generation but *before* rendering.

### 2. Data Flow
`Input File` -> `Loader` -> `DataFrame` -> `DataProcessor (Filter/Join)` -> `ChartEngine` -> `Image Bytes` -> `ReportSection` -> `OutputAdapter` -> `File`

### 3. Verification Claims
To ensure correctness, the system generates `NumberClaim` objects during processing.
*   **Concept**: When a number is rendered in a table, a claim is created: *"Value 100.5 appeared in row 0 column 'amount' derived from dataset 'sales'"*.
*   **Validator**: (Planned Phase) Re-checks these claims against the raw dataframe sum/count to ensure rendering didn't corrupt the data.

### 4. Component Styling
The `ThemeApplicator` converts the high-level YAML theme into:
1.  CSS Variables (for HTML).
2.  Matplotlib `rcParsms` (for Charts).
3.  PPTX Slide Master layouts (for PowerPoint).

This ensures visual consistency across disparate output media.
