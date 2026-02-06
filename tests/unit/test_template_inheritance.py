"""Tests for template inheritance and merging."""

import yaml

from pygramattic_reports.templates.loader import TemplateLoader


def test_template_inheritance(tmp_path):
    # 1. Create Parent Template
    parent_data = {
        "name": "parent",
        "description": "Base template",
        "sections": [
            {"type": "title", "content": "Default Title", "title": "Main Title"},
            {"type": "narrative", "content": "Base narrative", "title": "Intro"},
            {"type": "narrative", "content": "Footer info", "title": "Footer"},
        ],
        "metadata": {"author": "Base Corp"},
    }
    (tmp_path / "parent.yaml").write_text(yaml.dump(parent_data))

    # 2. Create Child Template
    child_data = {
        "name": "child",
        "extends": "parent",
        "sections": [
            # Override Intro
            {"type": "narrative", "content": "Child narrative override", "title": "Intro"},
            # Add New Section
            {"type": "heading", "content": "New Child Section", "title": "Specifics"},
        ],
        "metadata": {"version": "2.0"},
    }
    (tmp_path / "child.yaml").write_text(yaml.dump(child_data))

    # 3. Load Child
    loader = TemplateLoader(tmp_path)
    template = loader.load("child")

    # 4. Verify Merging
    assert template.name == "child"
    assert template.description == "Base template"  # Inherited
    assert template.metadata["author"] == "Base Corp"  # Inherited
    assert template.metadata["version"] == "2.0"  # Added/Overridden

    # Verify Sections
    # Expectations:
    # 1. Main Title (Inherited)
    # 2. Intro (Overridden)
    # 3. Footer (Inherited)
    # 4. Specifics (Appended)

    assert len(template.sections) == 4

    s0 = template.sections[0]
    assert s0.title == "Main Title"
    assert s0.content == "Default Title"

    s1 = template.sections[1]
    assert s1.title == "Intro"
    assert s1.content == "Child narrative override"  # OVERRIDDEN

    s2 = template.sections[2]
    assert s2.title == "Footer"

    s3 = template.sections[3]
    assert s3.title == "Specifics"
