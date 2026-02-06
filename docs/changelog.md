# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-02-06

### Added

- **Core Visualization Engine**
  - **Chart Engine**: Overhauled with support for 15+ chart types including Waterfall, Gauge, Funnel, Sankey, Treemap, and Radar.
  - **Advanced Charts**: Added support for reference lines, annotations, trend lines, and multi-chart subplots.
  - **Table System**: Major upgrade with totals rows, conditional formatting, and enhanced styling.

- **Document Structure & Layout**
  - **Output Formats**: Full support for HTML, PowerPoint (PPTX), Excel (XLSX), and Markdown outputs.
  - **Layout Elements**: New sections for Lists, Callouts (Info/Warning/Error), Metric Cards, Code Blocks, and Quotes.
  - **Multi-Column Layouts**: Support for 2-column and nested layouts.
  - **Metadata**: Support for cover pages, table of contents, headers, footers, and document properties.

- **Data Processing & Validation**
  - **Data Operations**: Filtering, sorting, aggregation, pivoting, and calculated columns.
  - **Data Joins**: Ability to merge multiple datasets using `apply_join`.
  - **Validation**: Built-in rules for data completeness, uniqueness, and range checking.
  - **Data Sources**: Loaders for CSV, Excel, JSON, Parquet, and Markdown/YAML.

- **AI Integration**
  - **Claude CLI**: Integration for generating summaries, insights, and anomaly detection.
  - **Fallbacks**: Robust fallback mechanisms when AI is unavailable.

- **Developer Experience**
  - **Fluent API**: New `Pygramattic` builder API for intuitive report construction.
  - **CLI Tools**: Enhanced `build`, `inspect`, and `validate` commands.
  - **Snapshot Testing**: Integrated snapshot testing for visual regression detection.
  - **Strict Typing**: Full MyPy strict mode compliance.

- **Documentation**
  - Comprehensive documentation suite including User Guide, API Reference, and Example Gallery.

### Changed

- Refactored `ReportBuilder` for better error handling and recoverability.
- Standardized Theme system with full CSS variable generation and easier inheritance.
- Moved to `pydantic-settings` v2 for configuration management.

### Fixed

- Resolved massive technical debt in type safety (700+ linting issues fixed).
- Fixed snapshot non-determinism in tests.

## [0.1.0] - Initial Beta
- Core functionality: Loaders, Builder, Charts, HTML Export.
