"""Tests for the template engine (Phase 10)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pygramattic_reports.exceptions import TemplateError
from pygramattic_reports.models import SectionSource, TemplateSectionSpec, TemplateSpec
from pygramattic_reports.templates import TemplateLoader, TemplateRenderer

# ---------- Helpers ----------------------------------------------------------

_SAMPLE_TEMPLATES = Path(__file__).resolve().parent.parent.parent / "sample_templates"


def _make_template(
    name: str = "test",
    sections: list[TemplateSectionSpec] | None = None,
) -> TemplateSpec:
    """Build a minimal TemplateSpec for testing."""
    if sections is None:
        sections = [
            TemplateSectionSpec(type="title", source=SectionSource.STATIC, content="Hello"),
        ]
    return TemplateSpec(name=name, sections=sections)


def _write_yaml(tmp_path: Path, name: str, content: str) -> Path:
    """Write a YAML file into a temp directory and return the directory."""
    path = tmp_path / f"{name}.yaml"
    path.write_text(content)
    return tmp_path


# ---------- Template Loader tests --------------------------------------------


class TestLoadTemplate:
    """Test loading a valid YAML template."""

    def test_load_template(self, tmp_path: Path) -> None:
        """Load a well-formed template YAML file."""
        yaml_content = """\
name: demo
description: A demo template
version: "1.0"
sections:
  - type: title
    source: static
    content: "Hello World"
  - type: data_table
    source: data
    title: "Data"
    dataset: my_data
"""
        templates_dir = _write_yaml(tmp_path, "demo", yaml_content)
        loader = TemplateLoader(templates_dir=templates_dir)
        template = loader.load("demo")

        assert template.name == "demo"
        assert len(template.sections) == 2
        assert template.sections[0].type == "title"
        assert template.sections[1].source == SectionSource.DATA


class TestLoadTemplateNotFound:
    """Test loading a nonexistent template."""

    def test_load_template_not_found(self, tmp_path: Path) -> None:
        """Raises TemplateError when template file missing."""
        loader = TemplateLoader(templates_dir=tmp_path)
        with pytest.raises(TemplateError, match="not found"):
            loader.load("nonexistent")


class TestLoadTemplateInvalidYaml:
    """Test loading an invalid YAML file."""

    def test_load_template_invalid_yaml(self, tmp_path: Path) -> None:
        """Raises TemplateError for malformed YAML."""
        bad_yaml = "name: test\nsections:\n  - [invalid: yaml: :"
        (tmp_path / "bad.yaml").write_text(bad_yaml)
        loader = TemplateLoader(templates_dir=tmp_path)
        with pytest.raises(TemplateError, match="Invalid YAML"):
            loader.load("bad")


class TestLoadTemplateMissingRequired:
    """Test loading a template missing required fields."""

    def test_load_template_missing_required(self, tmp_path: Path) -> None:
        """Raises TemplateError when required fields are absent."""
        yaml_content = "description: missing name and sections\n"
        _write_yaml(tmp_path, "incomplete", yaml_content)
        loader = TemplateLoader(templates_dir=tmp_path)
        with pytest.raises(TemplateError, match="Invalid template"):
            loader.load("incomplete")


class TestListTemplates:
    """Test listing available templates."""

    def test_list_templates(self, tmp_path: Path) -> None:
        """Lists all YAML template names sorted."""
        (tmp_path / "beta.yaml").write_text("name: beta\nsections: []\n")
        (tmp_path / "alpha.yaml").write_text("name: alpha\nsections: []\n")
        (tmp_path / "notes.txt").write_text("not a template")

        loader = TemplateLoader(templates_dir=tmp_path)
        names = loader.list_templates()

        assert names == ["alpha", "beta"]

    def test_list_templates_empty_dir(self, tmp_path: Path) -> None:
        """Returns empty list for directory with no templates."""
        loader = TemplateLoader(templates_dir=tmp_path)
        assert loader.list_templates() == []

    def test_list_templates_missing_dir(self) -> None:
        """Returns empty list when directory does not exist."""
        loader = TemplateLoader(templates_dir=Path("/nonexistent"))
        assert loader.list_templates() == []


class TestValidateTemplateWarnings:
    """Test template validation warnings."""

    def test_validate_template_warnings(self) -> None:
        """Returns warnings for incomplete sections."""
        template = TemplateSpec(
            name="warn_test",
            sections=[
                # Data section missing dataset
                TemplateSectionSpec(type="data_table", source=SectionSource.DATA),
                # Chart section missing chart_type, x_column, y_columns
                TemplateSectionSpec(type="chart", source=SectionSource.CHART),
                # AI section missing ai_prompt
                TemplateSectionSpec(type="summary", source=SectionSource.AI_GENERATED),
                # Duplicate titles
                TemplateSectionSpec(type="heading", source=SectionSource.STATIC, title="Dup"),
                TemplateSectionSpec(type="heading", source=SectionSource.STATIC, title="Dup"),
            ],
        )
        loader = TemplateLoader(templates_dir=Path())
        warnings = loader.validate(template)

        assert any("dataset" in w for w in warnings)
        assert any("chart_type" in w for w in warnings)
        assert any("x_column" in w for w in warnings)
        assert any("y_columns" in w for w in warnings)
        assert any("ai_prompt" in w for w in warnings)
        assert any("duplicate" in w for w in warnings)


# ---------- Template Renderer tests ------------------------------------------


class TestRenderStringSimple:
    """Test basic variable substitution."""

    def test_render_string_simple(self) -> None:
        """Variables resolved in template string."""
        renderer = TemplateRenderer()
        result = renderer.render_string(
            "Revenue Report: {{ report_title }}",
            context={"report_title": "Q4 2024 Analysis"},
        )
        assert result == "Revenue Report: Q4 2024 Analysis"

    def test_render_string_multiple_vars(self) -> None:
        """Multiple variables resolved correctly."""
        renderer = TemplateRenderer()
        result = renderer.render_string(
            "{{ name }} - {{ year }}",
            context={"name": "Sales", "year": "2024"},
        )
        assert result == "Sales - 2024"


class TestRenderStringMissingVar:
    """Test handling of undefined variables."""

    def test_render_string_missing_var_warn(self) -> None:
        """Warn mode renders missing vars as empty string."""
        renderer = TemplateRenderer(undefined_behavior="warn")
        result = renderer.render_string("Hello {{ missing }}", context={})
        assert result == "Hello "

    def test_render_string_missing_var_strict(self) -> None:
        """Strict mode raises TemplateError for missing vars."""
        renderer = TemplateRenderer(undefined_behavior="strict")
        with pytest.raises(TemplateError, match="Undefined variable"):
            renderer.render_string("Hello {{ missing }}", context={})

    def test_render_string_missing_var_ignore(self) -> None:
        """Ignore mode silently renders missing vars as empty string."""
        renderer = TemplateRenderer(undefined_behavior="ignore")
        result = renderer.render_string("Hello {{ missing }}", context={})
        assert result == "Hello "

    def test_invalid_undefined_behavior(self) -> None:
        """Invalid undefined_behavior raises ValueError."""
        with pytest.raises(ValueError, match="Invalid undefined_behavior"):
            TemplateRenderer(undefined_behavior="invalid")


class TestEvaluateConditionTrue:
    """Test condition evaluation returning true."""

    def test_evaluate_condition_true(self) -> None:
        """Truthy condition returns True."""
        renderer = TemplateRenderer()
        assert renderer.evaluate_condition("count > 0", {"count": 10}) is True

    def test_evaluate_condition_string_in(self) -> None:
        """String membership check works."""
        renderer = TemplateRenderer()
        assert (
            renderer.evaluate_condition("'revenue' in columns", {"columns": ["revenue", "cost"]})
            is True
        )


class TestEvaluateConditionFalse:
    """Test condition evaluation returning false."""

    def test_evaluate_condition_false(self) -> None:
        """Falsy condition returns False."""
        renderer = TemplateRenderer()
        assert renderer.evaluate_condition("count > 100", {"count": 5}) is False

    def test_evaluate_condition_error(self) -> None:
        """Malformed condition treated as false."""
        renderer = TemplateRenderer()
        assert renderer.evaluate_condition("???invalid!!!", {}) is False


class TestResolveTemplateFiltersSections:
    """Test conditional section filtering."""

    def test_resolve_template_filters_sections(self) -> None:
        """Sections with false conditions are excluded."""
        template = TemplateSpec(
            name="conditional",
            sections=[
                TemplateSectionSpec(
                    type="title",
                    source=SectionSource.STATIC,
                    content="{{ title }}",
                ),
                TemplateSectionSpec(
                    type="data_table",
                    source=SectionSource.DATA,
                    title="Hidden",
                    dataset="ds",
                    condition="show_data",
                ),
                TemplateSectionSpec(
                    type="narrative",
                    source=SectionSource.STATIC,
                    content="Always shown",
                ),
            ],
        )
        renderer = TemplateRenderer()
        resolved = renderer.resolve_template(template, {"title": "My Report", "show_data": False})

        assert len(resolved) == 2
        assert resolved[0].content == "My Report"
        assert resolved[1].content == "Always shown"


class TestResolveTemplatePreservesOrder:
    """Test section order preservation."""

    def test_resolve_template_preserves_order(self) -> None:
        """Resolved sections maintain original order."""
        template = TemplateSpec(
            name="ordered",
            sections=[
                TemplateSectionSpec(type="title", source=SectionSource.STATIC, content="First"),
                TemplateSectionSpec(type="heading", source=SectionSource.STATIC, content="Second"),
                TemplateSectionSpec(type="narrative", source=SectionSource.STATIC, content="Third"),
            ],
        )
        renderer = TemplateRenderer()
        resolved = renderer.resolve_template(template, {})

        assert [s.content for s in resolved] == ["First", "Second", "Third"]
        assert [s.type for s in resolved] == ["title", "heading", "narrative"]


class TestSampleTemplatesLoadable:
    """Test that the bundled sample templates can be loaded."""

    @pytest.mark.skipif(
        not _SAMPLE_TEMPLATES.is_dir(),
        reason="sample_templates directory not found",
    )
    def test_default_template_loads(self) -> None:
        """default.yaml loads and validates."""
        loader = TemplateLoader(templates_dir=_SAMPLE_TEMPLATES)
        template = loader.load("default")
        assert template.name == "default"
        assert len(template.sections) == 5

    @pytest.mark.skipif(
        not _SAMPLE_TEMPLATES.is_dir(),
        reason="sample_templates directory not found",
    )
    def test_quarterly_report_template_loads(self) -> None:
        """quarterly_report.yaml loads and validates."""
        loader = TemplateLoader(templates_dir=_SAMPLE_TEMPLATES)
        template = loader.load("quarterly_report")
        assert template.name == "quarterly_report"
        assert len(template.sections) == 10
