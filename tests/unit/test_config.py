"""Unit tests for the configuration system."""

import os
from pathlib import Path

import pytest

from pygramattic_reports.config import AppConfig, ConfigError, load_config
from pygramattic_reports.config.loader import deep_merge
from pygramattic_reports.config.settings import (
    ChartConfig,
    ClaudeConfig,
    DatabaseConfig,
    LoggingConfig,
    StorageConfig,
)


@pytest.fixture(autouse=True)
def _clean_config_env(monkeypatch):
    """Remove PYGRAMATTIC_ env vars and reset YAML data between tests."""
    for key in list(os.environ):
        if key.startswith("PYGRAMATTIC_"):
            monkeypatch.delenv(key)
    AppConfig.configure_yaml_data({})


# ---- Deep Merge ----


class TestDeepMerge:
    def test_flat_merge(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        base = {"top": {"a": 1, "b": 2}, "other": "x"}
        override = {"top": {"b": 3, "c": 4}}
        result = deep_merge(base, override)
        assert result == {"top": {"a": 1, "b": 3, "c": 4}, "other": "x"}

    def test_override_replaces_non_dict(self):
        base = {"a": {"nested": 1}}
        override = {"a": "flat_value"}
        result = deep_merge(base, override)
        assert result == {"a": "flat_value"}

    def test_empty_override(self):
        base = {"a": 1}
        result = deep_merge(base, {})
        assert result == {"a": 1}

    def test_empty_base(self):
        override = {"a": 1}
        result = deep_merge({}, override)
        assert result == {"a": 1}

    def test_does_not_mutate_inputs(self):
        base = {"a": {"b": 1}}
        override = {"a": {"c": 2}}
        deep_merge(base, override)
        assert base == {"a": {"b": 1}}
        assert override == {"a": {"c": 2}}


# ---- Default Configuration ----


class TestDefaultConfig:
    def test_default_config_no_files(self):
        config = load_config(config_dir=Path("/nonexistent/path"))
        assert config.environment == "development"
        assert config.storage.data_dir == Path("data")
        assert config.claude.max_retries == 3
        assert config.charts.default_dpi == 150

    def test_all_sub_configs_have_defaults(self):
        config = load_config(config_dir=Path("/nonexistent/path"))
        assert isinstance(config.storage, StorageConfig)
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.claude, ClaudeConfig)
        assert isinstance(config.charts, ChartConfig)
        assert isinstance(config.logging, LoggingConfig)

    def test_storage_defaults(self):
        config = load_config(config_dir=Path("/nonexistent/path"))
        assert config.storage.raw_dir == "raw"
        assert config.storage.processed_dir == "processed"
        assert config.storage.derived_dir == "derived"
        assert config.storage.reports_dir == "reports"
        assert config.storage.media_dir == "media"

    def test_database_defaults(self):
        config = load_config(config_dir=Path("/nonexistent/path"))
        assert config.database.host == "localhost"
        assert config.database.port == 5432
        assert config.database.read_only is True
        assert config.database.password == ""

    def test_claude_defaults(self):
        config = load_config(config_dir=Path("/nonexistent/path"))
        assert config.claude.enabled is True
        assert config.claude.executable == "claude"
        assert config.claude.timeout_seconds == 120

    def test_chart_defaults(self):
        config = load_config(config_dir=Path("/nonexistent/path"))
        assert config.charts.default_renderer == "matplotlib"
        assert config.charts.matplotlib_backend == "Agg"

    def test_logging_defaults(self):
        config = load_config(config_dir=Path("/nonexistent/path"))
        assert config.logging.level == "INFO"
        assert config.logging.format == "text"
        assert config.logging.log_file is None

    def test_path_defaults(self):
        config = load_config(config_dir=Path("/nonexistent/path"))
        assert config.templates_dir == Path("sample_templates")
        assert config.themes_dir == Path("sample_themes")
        assert config.configs_dir == Path("configs")


# ---- YAML Loading ----


class TestYamlLoading:
    def test_yaml_override(self, tmp_path):
        (tmp_path / "default.yaml").write_text("storage:\n  data_dir: /custom/data\n")
        config = load_config(config_dir=tmp_path)
        assert config.storage.data_dir == Path("/custom/data")

    def test_yaml_partial_override(self, tmp_path):
        (tmp_path / "default.yaml").write_text("claude:\n  max_retries: 5\n")
        config = load_config(config_dir=tmp_path)
        assert config.claude.max_retries == 5
        # Other claude defaults should still apply
        assert config.claude.enabled is True
        assert config.claude.timeout_seconds == 120

    def test_env_specific_yaml(self, tmp_path):
        (tmp_path / "default.yaml").write_text(
            "environment: development\nclaude:\n  enabled: true\n  max_retries: 3\n"
        )
        (tmp_path / "production.yaml").write_text(
            "environment: production\nclaude:\n  enabled: false\n"
        )
        config = load_config(config_dir=tmp_path, environment="production")
        assert config.environment == "production"
        assert config.claude.enabled is False
        # max_retries from default.yaml should be preserved
        assert config.claude.max_retries == 3

    def test_empty_yaml_uses_defaults(self, tmp_path):
        (tmp_path / "default.yaml").write_text("")
        config = load_config(config_dir=tmp_path)
        assert config.environment == "development"
        assert config.storage.data_dir == Path("data")

    def test_yaml_only_comment_uses_defaults(self, tmp_path):
        (tmp_path / "default.yaml").write_text("# just a comment\n")
        config = load_config(config_dir=tmp_path)
        assert config.environment == "development"

    def test_invalid_yaml_raises_config_error(self, tmp_path):
        (tmp_path / "default.yaml").write_text("invalid: yaml: content: [")
        with pytest.raises(ConfigError, match="Invalid YAML"):
            load_config(config_dir=tmp_path)

    def test_missing_env_yaml_is_ignored(self, tmp_path):
        (tmp_path / "default.yaml").write_text("environment: development\n")
        # No production.yaml exists - should not raise
        config = load_config(config_dir=tmp_path, environment="production")
        assert config.environment == "development"


# ---- Environment Variable Overrides ----


class TestEnvVarOverrides:
    def test_env_var_overrides_yaml(self, tmp_path, monkeypatch):
        (tmp_path / "default.yaml").write_text("claude:\n  enabled: true\n")
        monkeypatch.setenv("PYGRAMATTIC_CLAUDE__ENABLED", "false")
        config = load_config(config_dir=tmp_path)
        assert config.claude.enabled is False

    def test_env_var_overrides_default(self, monkeypatch):
        monkeypatch.setenv("PYGRAMATTIC_ENVIRONMENT", "staging")
        config = load_config(config_dir=Path("/nonexistent/path"))
        assert config.environment == "staging"

    def test_nested_env_var(self, monkeypatch):
        monkeypatch.setenv("PYGRAMATTIC_DATABASE__HOST", "db.example.com")
        monkeypatch.setenv("PYGRAMATTIC_DATABASE__PORT", "5433")
        config = load_config(config_dir=Path("/nonexistent/path"))
        assert config.database.host == "db.example.com"
        assert config.database.port == 5433

    def test_database_password_from_env(self, monkeypatch):
        monkeypatch.setenv("PYGRAMATTIC_DATABASE__PASSWORD", "secret123")
        config = load_config(config_dir=Path("/nonexistent/path"))
        assert config.database.password == "secret123"  # noqa: S105


# ---- Programmatic Overrides ----


class TestOverrides:
    def test_overrides_applied(self):
        config = load_config(
            config_dir=Path("/nonexistent/path"),
            overrides={"environment": "testing"},
        )
        assert config.environment == "testing"

    def test_overrides_beat_env_vars(self, monkeypatch):
        monkeypatch.setenv("PYGRAMATTIC_ENVIRONMENT", "from_env")
        config = load_config(
            config_dir=Path("/nonexistent/path"),
            overrides={"environment": "from_override"},
        )
        assert config.environment == "from_override"

    def test_overrides_beat_yaml(self, tmp_path):
        (tmp_path / "default.yaml").write_text("environment: from_yaml\n")
        config = load_config(
            config_dir=tmp_path,
            overrides={"environment": "from_override"},
        )
        assert config.environment == "from_override"

    def test_invalid_override_raises_config_error(self):
        with pytest.raises(ConfigError, match="Invalid configuration"):
            load_config(
                config_dir=Path("/nonexistent/path"),
                overrides={"database": "not_a_dict"},
            )


# ---- Environment Detection ----


class TestEnvironmentDetection:
    def test_default_environment(self):
        config = load_config(config_dir=Path("/nonexistent/path"))
        assert config.environment == "development"

    def test_explicit_environment(self, tmp_path):
        (tmp_path / "default.yaml").write_text("environment: development\n")
        (tmp_path / "staging.yaml").write_text("environment: staging\n")
        config = load_config(config_dir=tmp_path, environment="staging")
        assert config.environment == "staging"

    def test_environment_from_env_var(self, tmp_path, monkeypatch):
        (tmp_path / "default.yaml").write_text("environment: development\n")
        (tmp_path / "staging.yaml").write_text("environment: staging\n")
        monkeypatch.setenv("PYGRAMATTIC_ENVIRONMENT", "staging")
        config = load_config(config_dir=tmp_path)
        assert config.environment == "staging"
