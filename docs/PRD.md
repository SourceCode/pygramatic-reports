Product Requirements Document (PRD)

Product Name

Unified Python Report Processing & Generation Tool

Purpose

Build a clonable Python-based tool that ingests data from many sources, normalizes it, processes it, and generates consistent, validated, and well‑styled reports across multiple output formats. The system emphasizes repeatability, clarity, professional tone, and strong chart/graph craftsmanship.

Goals
	•	One consistent pipeline from raw data → structured datasets → validated reports
	•	Support a wide range of input/output formats used in analytics and reporting
	•	Enable template‑driven, theme‑driven report assembly
	•	Generate publication‑ready charts and graphs
	•	Validate report accuracy against source data
	•	Continuously improve reports via feedback loops

Non‑Goals
	•	Real‑time streaming analytics
	•	Interactive dashboards (this is a report generator, not BI tooling)
	•	Heavy ML modeling beyond summarization and validation

⸻

Target Users
	•	Data analysts
	•	Engineers
	•	Product and business stakeholders
	•	Report automation pipelines

⸻

Functional Requirements

1. Input Handling

Supported Input Files
	•	JSON
	•	CSV
	•	XLS / XLSX
	•	DOCX
	•	TXT
	•	MD
	•	Google Docs (.gdoc)
	•	Google Sheets (.gsheet)
	•	Google Slides (.gslides)

Supported Input Sources
	•	PostgreSQL (direct connection)

Requirements
	•	All inputs must be normalized into an internal canonical representation (JSON‑first)
	•	Large files should be streamed where possible
	•	Google formats require authenticated API access and conversion

⸻

2. Data Conversion

Converters
	•	Dataset → JSON
	•	Dataset → SQL (DDL + INSERTs)

Requirements
	•	Schema inference for tabular data
	•	Explicit data typing (string, int, float, date, boolean)
	•	Deterministic and reproducible output

⸻

3. Storage System

Data Directory Structure
A standardized data/ directory:

data/
  raw/
  processed/
  derived/
  reports/
  media/

Requirements
	•	Programmatic directory creation
	•	Type‑based and report‑based organization
	•	Metadata file (manifest.json) per dataset

⸻

4. Templates & Themes

Templates
	•	Control layout and structure
	•	Define sections, ordering, and placeholders

Themes
	•	Control styling
	•	Fonts, colors, spacing, chart styles

Requirements
	•	Templates and themes must be swappable
	•	Declarative configuration (YAML or JSON)
	•	Output‑agnostic design (Docx, Markdown, Slides)

⸻

5. Report Builder

Core Capabilities
	•	Assemble reports from templates + themes
	•	Inject processed datasets
	•	Generate charts, tables, images
	•	Embed media into reports

Claude CLI Integration (Headless)
	•	Used for:
	•	Content summarization
	•	Section drafting
	•	Narrative consistency
	•	Prompt characteristics:
	•	Concise
	•	Clear
	•	Professional tone
	•	High‑school freshman reading level
	•	Avoid complex or technical wording

Common Function Library
Spreadsheet‑like operations:
	•	Aggregations (sum, avg, min, max)
	•	Joins
	•	Filters
	•	Window functions
	•	Percent change
	•	Ratios

Data Processors
	•	Text
	•	Table
	•	Chart
	•	Graph
	•	Spreadsheet
	•	Image

⸻

6. Report Validator

Purpose
Ensure the generated report accurately reflects the underlying data.

Functionality
	•	Re‑parse final output
	•	Validate numerical claims against datasets
	•	Claude CLI used in headless mode with strict validation prompts

Output
	•	Validation report (pass/fail + discrepancies)

⸻

7. Chart & Graph Generator

Supported Libraries
Matplotlib + Seaborn
	•	PNG / SVG / PDF via savefig()

Plotly + Kaleido
	•	PNG / SVG / PDF via static export

Standards
	•	Clear titles
	•	Clearly labeled axes (always)
	•	Consistent theme styling
	•	Deterministic rendering

⸻

8. Feedback Tool

Purpose
Continuously improve report quality using edited reports as feedback.

Functionality
	•	Compare last generated report vs edited version
	•	Claude CLI analyzes differences
	•	Adjust prompts, structure, verbosity, or data emphasis

Common Feedback Patterns
	•	Make reports more concise
	•	Update specific figures
	•	Adjust narrative focus

⸻

9. Output Formats

Structured
	•	JSON
	•	CSV
	•	SQL

Documents
	•	DOCX
	•	XLS / XLSX
	•	TXT
	•	MD
	•	GDoc
	•	GSheet
	•	GSlides

Media
	•	PNG
	•	JPEG
	•	AVIF
	•	WebP

⸻

Quality Attributes
	•	Deterministic outputs
	•	Reproducible builds
	•	Clear error messages
	•	Extensible architecture
	•	Strong separation of concerns

⸻

Technical Specification

Architecture Overview

inputs → loaders → normalizers → processors → builders → validators → outputs


⸻

Repository Structure

repo/
  src/
    loaders/
    converters/
    storage/
    processors/
    charts/
    templates/
    themes/
    builder/
    validator/
    feedback/
    cli/
  data/
  configs/
  tests/


⸻

Core Modules

1. Loaders

Responsibilities:
	•	Read files and databases
	•	Authenticate with Google APIs

Interfaces:
	•	load(input_config) -> RawData

⸻

2. Normalizers

Responsibilities:
	•	Convert raw input to canonical JSON

Interfaces:
	•	normalize(raw_data) -> Dataset

⸻

3. Converters

Responsibilities:
	•	Dataset ↔ JSON
	•	Dataset ↔ SQL

Interfaces:
	•	to_json(dataset)
	•	to_sql(dataset)

⸻

4. Storage Manager

Responsibilities:
	•	Directory creation
	•	Dataset persistence
	•	Metadata tracking

⸻

5. Processor Engine

Responsibilities:
	•	Transform datasets
	•	Compute derived metrics

Design:
	•	Stateless functions
	•	Pandas‑based core

⸻

6. Chart Engine

Responsibilities:
	•	Chart generation
	•	Theme application

Design:
	•	Abstract chart spec → renderer
	•	Library‑agnostic interface

⸻

7. Template Engine

Responsibilities:
	•	Parse templates
	•	Inject content

Design:
	•	Jinja‑style rendering

⸻

8. Claude CLI Integration

Execution:
	•	Headless subprocess calls
	•	Strict prompt templates

Failure Handling:
	•	Retries
	•	Fallback summaries

⸻

9. Validator

Responsibilities:
	•	Cross‑check values
	•	Produce validation report

⸻

10. Feedback Engine

Responsibilities:
	•	Diff reports
	•	Update generation logic

⸻

Configuration
	•	YAML‑based config
	•	Environment‑specific overrides

⸻

CLI Interface

Examples:

report ingest data.csv
report build report.yaml
report validate report.docx
report feedback edited.docx


⸻

Testing Strategy
	•	Unit tests per module
	•	Golden file tests for reports
	•	Deterministic chart output tests

⸻

Security & Compliance
	•	Secrets via env vars
	•	Read‑only DB access where possible
	•	No data exfiltration

⸻

Future Extensions
	•	PDF first‑class support
	•	Versioned report diffs
	•	Multi‑language reports
	•	Scheduled batch execution

⸻

Success Metrics
	•	Time to generate report
	•	Validation pass rate
	•	Reduction in manual edits
	•	Consistency across outputs
