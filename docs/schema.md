# Data Schema & Models

Pygramattic Reports uses Pydantic specifically to enforce strict schemas for configuration and internal data structures.

## Core Entities

### Dataset
The fundamental unit of data.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` | Unique identifier (slug). |
| `dataframe` | `pd.DataFrame` | The actual data (Pandas). |
| `schema` | `list[ColumnSpec]` | Metadata about columns (name, type, validation rules). |
| `provenance` | `Provenance` | History of where this data came from and transformations applied. |

### TemplateSpec (`.yaml`)
Defines the structure of a report.

| Field | Type | Description |
| :--- | :--- | :--- |
| `name` | `str` | Internal name of the template. |
| `extends` | `str?` | Parent template ID. |
| `sections` | `list[Section]` | Ordered list of content blocks. |
| `page_layout` | `PageLayout` | Margins, orientation, size. |

### SectionSpec
A single block of content.

| Field | Type | Description |
| :--- | :--- | :--- |
| `type` | `str` | `narrative`, `chart`, `data_table`, `callout`, etc. |
| `source` | `enum` | `static`, `data`, `ai_generated`. |
| `content` | `str` | Raw text or Jinja2 template. |
| `dataset` | `str` | Reference to a loaded dataset ID. |
| `filters` | `list` | Data filtering rules. |
| `joins` | `list` | Join definitions. |
| `validation_rules` | `list` | Quality checks (`unique`, `completeness`). |

### ThemeSpec (`.yaml`)
Defines the visual style.

| Field | Type | Description |
| :--- | :--- | :--- |
| `colors` | `ColorSpec` | `primary`, `secondary`, `accent`, `background`, `text`. |
| `fonts` | `FontSpec` | Families and sizes. |
| `chart` | `ChartTheme` | Matplotlib specific overrides (grid, ticks, spines). |

## Database Schema
*This project is currently stateless and does not maintain a persistent relational database. All state is ephemeral during the build process or persisted as configuration files.*
