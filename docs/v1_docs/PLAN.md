# V1 Implementation Plan: Pygramattic Reports

## Overview

This plan breaks the PRD into **20 phases**, ordered by dependency. Each phase is self-contained, produces testable output, and is optimized for AI coding agents.

## Phase Summary

| Phase | Name | Key Deliverables | Dependencies |
|-------|------|-----------------|--------------|
| 01 | [Project Scaffold](./phase_01_project_scaffold.md) | pyproject.toml, directory structure, dev tooling | None |
| 02 | [Core Data Models](./phase_02_core_data_models.md) | Pydantic models: Dataset, Report, ChartSpec, etc. | Phase 01 |
| 03 | [Configuration System](./phase_03_configuration_system.md) | YAML config, env vars, AppConfig | Phase 01, 02 |
| 04 | [Logging & Error Handling](./phase_04_logging_error_handling.md) | structlog setup, exception hierarchy, BuildLog | Phase 01, 02, 03 |
| 05 | [Storage Manager](./phase_05_storage_manager.md) | data/ directory, manifests, save/load datasets | Phase 01-04 |
| 06 | [CSV & JSON Loaders](./phase_06_csv_json_loaders.md) | Loader base class, registry, CSV/JSON loaders, TabularNormalizer | Phase 01-05 |
| 07 | [Extended Loaders](./phase_07_extended_loaders.md) | XLSX, DOCX, TXT, MD loaders, DocumentNormalizer | Phase 06 |
| 08 | [CLI Foundation](./phase_08_cli_foundation.md) | Typer app, `report ingest`, `report list`, `report init` | Phase 06, 07, 05 |
| 09 | [Data Converters](./phase_09_data_converters.md) | to_json(), to_sql(), to_csv() | Phase 02, 04 |
| 10 | [Template Engine](./phase_10_template_engine.md) | YAML template loading, Jinja2 rendering, sample templates | Phase 02, 04 |
| 11 | [Theme Engine](./phase_11_theme_engine.md) | YAML theme loading, format-specific style translation | Phase 02, 04 |
| 12 | [Chart Engine](./phase_12_chart_engine.md) | Matplotlib renderer, 10 chart types, theme application | Phase 02, 04, 11 |
| 13 | [Report Builder (Core)](./phase_13_report_builder.md) | Report assembly, section processors, common functions | Phase 05, 10, 11, 12 |
| 14 | [Markdown Output](./phase_14_markdown_output.md) | Markdown adapter, table formatting, image references | Phase 13 |
| 15 | [DOCX Output](./phase_15_docx_output.md) | DOCX adapter, XLSX adapter, output registry | Phase 13, 11 |
| 16 | [CLI Build & Export](./phase_16_cli_build_export.md) | `report build`, `report export` commands | Phase 08, 13, 14, 15, 09 |
| 17 | [Claude CLI Integration](./phase_17_claude_cli_integration.md) | ClaudeClient, prompt templates, retry logic, fallbacks | Phase 03, 04 |
| 18 | [AI Report Sections](./phase_18_ai_report_sections.md) | AI-powered summaries and narratives in reports | Phase 13, 17 |
| 19 | [Report Validator](./phase_19_report_validator.md) | Structural, numerical, narrative validation | Phase 13, 17, 02 |
| 20 | [Feedback & Final CLI](./phase_20_feedback_and_final_cli.md) | Feedback engine, `report validate`, `report feedback`, E2E test | Phase 13, 17, 19 |

## Dependency Graph

```
Phase 01 ──→ Phase 02 ──→ Phase 03 ──→ Phase 04
                │              │            │
                ├──────────────┼────────────┤
                │              │            │
                ▼              ▼            ▼
            Phase 05       Phase 09    Phase 17
                │                          │
                ▼                          │
            Phase 06                       │
                │                          │
                ▼                          │
            Phase 07                       │
                │                          │
                ▼                          │
            Phase 08                       │
                                           │
Phase 02 ──→ Phase 10                      │
         ──→ Phase 11 ──→ Phase 12         │
                │              │           │
                └──────┬───────┘           │
                       ▼                   │
                   Phase 13 ───────────────┤
                   │   │   │               │
                   ▼   ▼   ▼               ▼
             Ph14  Ph15  Ph16          Phase 18
                              │            │
                              ▼            ▼
                          Phase 19 ←───Phase 17
                              │
                              ▼
                          Phase 20
```

## Parallelism Opportunities

Phases that can be worked on simultaneously by different agents:

- **Parallel Track A** (Phases 09, 10, 11): Converters, Templates, Themes are independent
- **Parallel Track B** (Phase 17): Claude CLI integration is independent of Phases 09-16
- **Parallel Track C** (Phases 14, 15): Markdown and DOCX adapters are independent of each other

## Architecture Pipeline

```
inputs → loaders → normalizers → processors → builders → validators → outputs
           │            │            │            │            │           │
       Phase 06-07   Phase 06-07  Phase 13    Phase 13     Phase 19   Phase 14-15
```

## PRD Coverage Matrix

| PRD Section | Phase(s) | Status |
|-------------|----------|--------|
| Input Handling (files) | 06, 07 | Full V1 coverage |
| Input Handling (PostgreSQL) | -- | Deferred to V2 |
| Input Handling (Google) | -- | Deferred to V2 |
| Data Conversion | 09 | Full coverage |
| Storage System | 05 | Full coverage |
| Templates & Themes | 10, 11 | Full coverage |
| Report Builder | 13, 18 | Full coverage |
| Claude CLI Integration | 17, 18 | Full coverage |
| Report Validator | 19 | Full coverage |
| Chart & Graph Generator | 12 | Matplotlib full, Plotly deferred |
| Feedback Tool | 20 | V1: advisory only (per recommendation) |
| Output: JSON, CSV, SQL | 09 | Full coverage |
| Output: MD | 14 | Full coverage |
| Output: DOCX | 15 | Full coverage |
| Output: XLSX | 15 | Full coverage |
| Output: Google formats | -- | Deferred to V2 |
| Output: Media (PNG) | 12 | Full coverage (via chart engine) |
| Output: Media (JPEG, AVIF, WebP) | -- | Deferred to V2 |
| CLI Interface | 08, 16, 20 | Full coverage |
| Common Function Library | 13 | Full coverage |
| Configuration | 03 | Full coverage |
| Testing Strategy | All phases | Unit + integration + E2E |
| Security & Compliance | 03 (env vars), 04 (errors) | Full coverage |

## Items Deferred to V2+

These PRD items are intentionally deferred based on the product review's risk assessment:

1. **PostgreSQL loader** -- Requires DB infrastructure, adds complexity
2. **Google Docs/Sheets/Slides** -- OAuth2 complexity, API quotas
3. **Plotly chart renderer** -- Matplotlib covers all V1 needs
4. **AVIF/WebP media output** -- Minimal user value for V1
5. **Automatic feedback application** -- V1 feedback is advisory only
6. **PDF output** -- Recommended for V1 by product review, but adds weasyprint dependency
7. **Scheduled batch execution** -- Future extension per PRD

## Key Technical Decisions

1. **Data models first** (Phase 02) -- All inter-module contracts defined upfront
2. **AI is optional** -- Every feature works without Claude CLI
3. **Vertical slice first** -- CSV-in, Markdown-out is the first complete path
4. **Deterministic by default** -- Matplotlib Agg backend, pinned versions
5. **Three-layer validation** -- Structural + numerical (deterministic) + narrative (AI)
6. **Feedback is advisory** -- No self-modifying behavior in V1
