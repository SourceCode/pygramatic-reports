# Phase 03: Configuration System

## Objective

Build a typed, layered configuration system that supports YAML config files, environment variable overrides, and CLI flag overrides. This system provides every module with its runtime settings.

## Why This Phase Is Third

The PRD specifies "YAML-based config" with "environment-specific overrides." Nearly every module needs configuration (data directory paths, database credentials, Claude CLI settings, chart defaults). Building this before any module avoids hardcoded values and enables testing with custom configs.

## Tasks

### Task 3.1: Define the Application Configuration Model

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/config/settings.py`

**Description:** Define a comprehensive Pydantic Settings model that represents all application configuration.

**Requirements:**
- Use `pydantic-settings` for environment variable support
- Override precedence: defaults < `configs/default.yaml` < `configs/{env}.yaml` < env vars < CLI flags
- Environment variable prefix: `PYGRAMATTIC_`
- All secrets (DB password, Google credentials path, Claude API key) come from env vars, never from YAML files

**Model structure:**

```python
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class StorageConfig(BaseModel):
    """Configuration for the storage subsystem."""
    data_dir: Path = Path("data")
    raw_dir: str = "raw"
    processed_dir: str = "processed"
    derived_dir: str = "derived"
    reports_dir: str = "reports"
    media_dir: str = "media"


class DatabaseConfig(BaseModel):
    """PostgreSQL connection configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = ""
    schema_name: str = "public"
    username: str = ""
    password: str = ""           # Populated from env var PYGRAMATTIC_DB_PASSWORD
    read_only: bool = True


class ClaudeConfig(BaseModel):
    """Claude CLI integration configuration."""
    enabled: bool = True
    executable: str = "claude"       # Path to Claude CLI binary
    timeout_seconds: int = 120
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    default_max_tokens: int = 1024


class ChartConfig(BaseModel):
    """Default chart rendering configuration."""
    default_renderer: str = "matplotlib"
    default_format: str = "png"
    default_dpi: int = 150
    default_width: int = 800
    default_height: int = 600
    matplotlib_backend: str = "Agg"    # Non-interactive backend for determinism


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "text"            # "text" or "json"
    log_file: Path | None = None
    log_ai_interactions: bool = False  # Log Claude prompts/responses


class AppConfig(BaseSettings):
    """Root application configuration.

    Load order:
    1. Field defaults (defined here)
    2. YAML config file (configs/default.yaml)
    3. Environment-specific YAML (configs/{env}.yaml)
    4. Environment variables (PYGRAMATTIC_*)
    5. CLI overrides (passed programmatically)
    """
    model_config = {"env_prefix": "PYGRAMATTIC_", "env_nested_delimiter": "__"}

    environment: str = "development"
    storage: StorageConfig = StorageConfig()
    database: DatabaseConfig = DatabaseConfig()
    claude: ClaudeConfig = ClaudeConfig()
    charts: ChartConfig = ChartConfig()
    logging: LoggingConfig = LoggingConfig()

    # Paths
    templates_dir: Path = Path("sample_templates")
    themes_dir: Path = Path("sample_themes")
    configs_dir: Path = Path("configs")
```

---

### Task 3.2: Build the Configuration Loader

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/config/loader.py`

**Description:** Implement YAML config file loading with environment-specific overrides and merge logic.

**Requirements:**
- Load `configs/default.yaml` as the base
- If `configs/{environment}.yaml` exists, deep-merge it over the defaults
- Environment variables override YAML values
- Return a fully validated `AppConfig` instance
- Raise `ConfigError` (from Phase 04) with clear message if config is invalid

**Interface:**
```python
def load_config(
    config_dir: Path | None = None,
    environment: str | None = None,
    overrides: dict | None = None,
) -> AppConfig:
    """Load and merge configuration from all sources.

    Args:
        config_dir: Path to configs directory. Defaults to ./configs/
        environment: Environment name (e.g., "development", "production").
                     Defaults to PYGRAMATTIC_ENVIRONMENT env var or "development".
        overrides: Additional overrides applied last (from CLI flags).

    Returns:
        Fully resolved AppConfig.

    Raises:
        ConfigError: If configuration is invalid.
    """
```

**Deep merge logic:**
```python
def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Override values win."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
```

---

### Task 3.3: Create Default Configuration File

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/configs/default.yaml`

**Content:**
```yaml
# Default configuration for pygramattic-reports
# Override with environment-specific files (e.g., production.yaml)
# or environment variables (PYGRAMATTIC_*)

environment: development

storage:
  data_dir: data
  raw_dir: raw
  processed_dir: processed
  derived_dir: derived
  reports_dir: reports
  media_dir: media

database:
  host: localhost
  port: 5432
  database: ""
  schema_name: public
  read_only: true

claude:
  enabled: true
  executable: claude
  timeout_seconds: 120
  max_retries: 3
  retry_backoff_factor: 2.0
  default_max_tokens: 1024

charts:
  default_renderer: matplotlib
  default_format: png
  default_dpi: 150
  default_width: 800
  default_height: 600
  matplotlib_backend: Agg

logging:
  level: INFO
  format: text
  log_file: null
  log_ai_interactions: false

templates_dir: sample_templates
themes_dir: sample_themes
```

---

### Task 3.4: Create Config Package Init

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/src/pygramattic_reports/config/__init__.py`

```python
"""Configuration management for pygramattic-reports.

Usage:
    from pygramattic_reports.config import load_config

    config = load_config()
    print(config.storage.data_dir)
"""
from .loader import load_config
from .settings import AppConfig

__all__ = ["load_config", "AppConfig"]
```

---

### Task 3.5: Write Configuration Tests

**File to create:** `/Volumes/SecondDrive/code2/pygramattic-reports/tests/unit/test_config.py`

**Test cases:**
1. Load default config with no files present -- should use all defaults
2. Load config from a YAML file -- should override defaults
3. Environment-specific YAML merges correctly over defaults
4. Environment variables override YAML values
5. Invalid YAML raises `ConfigError`
6. Missing required fields (if any) raise `ConfigError`
7. Deep merge handles nested dicts correctly
8. Programmatic overrides are applied last

**Example:**
```python
def test_default_config():
    config = load_config(config_dir=Path("/nonexistent"))
    assert config.environment == "development"
    assert config.storage.data_dir == Path("data")
    assert config.claude.max_retries == 3


def test_yaml_override(tmp_path):
    yaml_content = "storage:\n  data_dir: /custom/data\n"
    (tmp_path / "default.yaml").write_text(yaml_content)
    config = load_config(config_dir=tmp_path)
    assert config.storage.data_dir == Path("/custom/data")


def test_env_var_override(monkeypatch, tmp_path):
    monkeypatch.setenv("PYGRAMATTIC_CLAUDE__ENABLED", "false")
    config = load_config(config_dir=tmp_path)
    assert config.claude.enabled is False
```

---

## Dependencies

- **Depends on:** Phase 01 (project scaffold), Phase 02 (models -- for type references)
- **Blocks:** Phase 04 (logging uses config), Phase 05 (storage uses config), Phase 06+ (all modules use config)

## Acceptance Criteria

1. `load_config()` returns a valid `AppConfig` with all defaults populated
2. YAML files are loaded and merged correctly
3. Environment variables override YAML values
4. Invalid configuration produces clear error messages
5. All configuration tests pass
6. No secrets are stored in YAML files (only env vars)

## References

- PRD Configuration: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 367-369)
- PRD Security: `/Volumes/SecondDrive/code2/pygramattic-reports/docs/PRD.md` (lines 392-395)
