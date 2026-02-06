# Phase 10: Template Engine

## Objective

Build the template engine that parses YAML template definitions, resolves section specifications, and supports Jinja2-style variable interpolation. Templates define the structure and content of reports.

## Why This Phase Is Tenth

The Report Builder (Phase 13) requires templates to know what sections to assemble. Templates must be loadable and parseable before the builder can function. This phase establishes the template contract.

## Tasks

### Task 10.1: Implement the Template Loader

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/templates/loader.py`

**Description:** Load and validate template YAML files into `TemplateSpec` models.

**Requirements:**
- Read YAML files from the configured `templates_dir`
- Validate against the `TemplateSpec` Pydantic model (from Phase 02)
- Support listing available templates
- Raise `TemplateError` with clear messages for invalid templates

**Interface:**
```python
from pathlib import Path
from pygramattic_reports.models import TemplateSpec


class TemplateLoader:
    """Loads and validates report templates from YAML files.

    Templates are stored as YAML files in the templates directory.
    Each file defines one template.

    Usage:
        loader = TemplateLoader(templates_dir=Path("sample_templates"))
        template = loader.load("quarterly_report")
        all_templates = loader.list_templates()
    """

    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir

    def load(self, template_name: str) -> TemplateSpec:
        """Load a template by name.

        Looks for {templates_dir}/{template_name}.yaml

        Raises:
            TemplateError: If template not found or invalid.
        """
        ...

    def list_templates(self) -> list[str]:
        """List all available template names."""
        ...

    def validate(self, template: TemplateSpec) -> list[str]:
        """Validate a template and return any warnings.

        Checks:
        - All sections have valid types
        - Data-sourced sections reference a dataset name
        - Chart sections have required fields (chart_type, x_column, y_columns)
        - AI sections have a prompt
        - No duplicate section titles
        """
        ...
```

---

### Task 10.2: Implement the Template Renderer

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/templates/renderer.py`

**Description:** Resolve Jinja2 template strings within section content and titles, binding template variables to actual data values.

**Requirements:**
- Use `jinja2` for variable interpolation in section content and titles
- Template variables include:
  - `report_title` -- from report config
  - `report_date` -- build timestamp
  - `dataset_name` -- name of each dataset
  - Any key from the dataset metadata
  - Computed values (from processors)
- Support conditional sections: render section only if a Jinja2 condition evaluates to true
- Handle missing variables gracefully (log warning, render as empty string rather than crashing)

**Interface:**
```python
from jinja2 import Environment
from pygramattic_reports.models import TemplateSpec, TemplateSectionSpec


class TemplateRenderer:
    """Resolves Jinja2 template expressions in template sections.

    This does NOT produce the final report output. It resolves
    template variables ({{report_title}}, {{dataset.name}}) into
    concrete values. The Builder then uses these resolved sections
    to assemble the report.

    Usage:
        renderer = TemplateRenderer()
        resolved_content = renderer.render_string(
            "Revenue Report: {{report_title}}",
            context={"report_title": "Q4 2024 Analysis"}
        )
    """

    def __init__(self, undefined_behavior: str = "warn"):
        """
        Args:
            undefined_behavior: How to handle undefined variables.
                "warn" -- log warning, render as empty string
                "strict" -- raise TemplateError
                "ignore" -- silently render as empty string
        """
        ...

    def render_string(self, template_string: str, context: dict) -> str:
        """Render a single Jinja2 template string with the given context."""
        ...

    def evaluate_condition(self, condition: str, context: dict) -> bool:
        """Evaluate a Jinja2 conditional expression.

        Used for conditional section rendering.
        Example: "datasets.revenue.row_count > 0"
        """
        ...

    def resolve_template(
        self, template: TemplateSpec, context: dict
    ) -> list[TemplateSectionSpec]:
        """Resolve all template sections with the given context.

        - Renders Jinja2 expressions in section content and titles
        - Filters out sections whose conditions evaluate to false
        - Returns the resolved list of sections

        Args:
            template: The template specification
            context: Variable bindings (report metadata, dataset info, etc.)

        Returns:
            List of resolved section specs ready for the Builder.
        """
        ...
```

---

### Task 10.3: Create Default Template

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/sample_templates/default.yaml`

**Description:** A simple default template that works for any single-dataset report.

```yaml
name: default
description: A simple default report template suitable for any single dataset
version: "1.0"

sections:
  - type: title
    source: static
    content: "{{ report_title }}"

  - type: summary
    source: ai_generated
    title: "Executive Summary"
    ai_prompt: >
      Write a brief executive summary (2-3 paragraphs) of the data in
      the dataset "{{ dataset_name }}". Focus on key trends, notable
      values, and overall patterns. Use a professional but accessible
      tone at a high-school freshman reading level.
    ai_max_words: 200

  - type: data_table
    source: data
    title: "Data Overview"
    dataset: "{{ primary_dataset }}"

  - type: chart
    source: chart
    title: "Visualization"
    dataset: "{{ primary_dataset }}"
    chart_type: bar
    x_column: "{{ x_column }}"
    y_columns: ["{{ y_column }}"]

  - type: narrative
    source: ai_generated
    title: "Analysis"
    ai_prompt: >
      Analyze the key findings from the dataset "{{ dataset_name }}".
      Highlight important trends, outliers, and actionable insights.
      Keep the language clear and concise.
    ai_max_words: 300
```

---

### Task 10.4: Create Quarterly Report Template

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/sample_templates/quarterly_report.yaml`

**Description:** A more structured template for quarterly business reports.

```yaml
name: quarterly_report
description: Quarterly business report with revenue, growth, and regional breakdown
version: "1.0"

sections:
  - type: title
    source: static
    content: "{{ report_title }}"

  - type: heading
    source: static
    content: "Report Period: {{ report_period }}"
    level: 2

  - type: summary
    source: ai_generated
    title: "Executive Summary"
    ai_prompt: >
      Write a concise executive summary of the quarterly performance data.
      Cover overall revenue, growth trends, and regional highlights.
      Keep it to 2-3 paragraphs at a high-school freshman reading level.
    ai_max_words: 200

  - type: data_table
    source: data
    title: "Revenue by Region"
    dataset: main_data

  - type: chart
    source: chart
    title: "Revenue Distribution"
    dataset: main_data
    chart_type: bar
    x_column: region
    y_columns: ["revenue"]

  - type: chart
    source: chart
    title: "Growth Trends"
    dataset: main_data
    chart_type: line
    x_column: quarter
    y_columns: ["growth_pct"]
    condition: "'growth_pct' in dataset_columns"

  - type: narrative
    source: ai_generated
    title: "Detailed Analysis"
    ai_prompt: >
      Provide a detailed analysis of the quarterly data. Discuss regional
      performance differences, growth trajectory, and any concerning trends.
      Suggest areas for investigation. Professional tone, clear language.
    ai_max_words: 400

  - type: page_break
    source: static

  - type: heading
    source: static
    content: "Appendix"
    level: 2

  - type: data_table
    source: data
    title: "Full Dataset"
    dataset: main_data
```

---

### Task 10.5: Create Templates Package Init

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/templates/__init__.py`

```python
"""Template engine for pygramattic-reports.

Load, validate, and render report templates.

Usage:
    from pygramattic_reports.templates import TemplateLoader, TemplateRenderer

    loader = TemplateLoader(templates_dir)
    template = loader.load("quarterly_report")

    renderer = TemplateRenderer()
    resolved = renderer.resolve_template(template, context)
"""
from .loader import TemplateLoader
from .renderer import TemplateRenderer

__all__ = ["TemplateLoader", "TemplateRenderer"]
```

---

### Task 10.6: Write Template Tests

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_templates.py`

**Test cases:**

**Template Loader:**
1. `test_load_template` -- Load a valid YAML template
2. `test_load_template_not_found` -- Raises `TemplateError`
3. `test_load_template_invalid_yaml` -- Raises `TemplateError`
4. `test_load_template_missing_required` -- Raises `TemplateError` for missing name/sections
5. `test_list_templates` -- Lists all templates in directory
6. `test_validate_template_warnings` -- Returns warnings for incomplete sections

**Template Renderer:**
7. `test_render_string_simple` -- Variable substitution works
8. `test_render_string_missing_var` -- Missing variable handled gracefully
9. `test_evaluate_condition_true` -- Condition evaluates to true
10. `test_evaluate_condition_false` -- Condition evaluates to false
11. `test_resolve_template_filters_sections` -- Conditional sections filtered out
12. `test_resolve_template_preserves_order` -- Section order maintained

---

## Dependencies

- **Depends on:** Phase 02 (TemplateSpec model), Phase 04 (TemplateError)
- **Blocks:** Phase 13 (Builder uses templates)

## Acceptance Criteria

1. `TemplateLoader` loads and validates YAML templates
2. `TemplateRenderer` resolves Jinja2 expressions in templates
3. Conditional sections are correctly filtered
4. Default and quarterly_report templates exist and validate
5. All tests pass

## References

- PRD Templates & Themes: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 91-104)
- PRD Template Engine Module: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 328-336)
