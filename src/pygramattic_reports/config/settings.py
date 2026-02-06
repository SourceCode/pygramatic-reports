"""Application configuration models for pygramattic-reports.

Defines all typed configuration sections and the root ``AppConfig``
settings model with support for YAML files, environment variables,
and programmatic overrides.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo


class StorageConfig(BaseModel):
    """Configuration for the storage subsystem.

    Attributes:
        data_dir: Root data directory.
        raw_dir: Raw data subdirectory name.
        processed_dir: Processed data subdirectory name.
        derived_dir: Derived data subdirectory name.
        reports_dir: Reports output subdirectory name.
        media_dir: Media (charts, images) subdirectory name.
    """

    data_dir: Path = Path("data")
    raw_dir: str = "raw"
    processed_dir: str = "processed"
    derived_dir: str = "derived"
    reports_dir: str = "reports"
    media_dir: str = "media"


class DatabaseConfig(BaseModel):
    """PostgreSQL connection configuration.

    Attributes:
        host: Database server hostname.
        port: Database server port.
        database: Database name.
        schema_name: Default database schema.
        username: Database username (prefer env var ``PYGRAMATTIC_DATABASE__USERNAME``).
        password: Database password (prefer env var ``PYGRAMATTIC_DATABASE__PASSWORD``).
        read_only: Whether to use read-only connections.
    """

    host: str = "localhost"
    port: int = 5432
    database: str = ""
    schema_name: str = "public"
    username: str = ""
    password: str = ""
    read_only: bool = True


class ClaudeConfig(BaseModel):
    """Claude CLI integration configuration.

    Attributes:
        enabled: Whether Claude CLI integration is active.
        executable: Path to the Claude CLI binary.
        timeout_seconds: Maximum seconds to wait for a Claude response.
        max_retries: Number of retry attempts on failure.
        retry_backoff_factor: Exponential backoff multiplier.
        default_max_tokens: Default token limit for Claude responses.
    """

    enabled: bool = True
    executable: str = "claude"
    timeout_seconds: int = 120
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    default_max_tokens: int = 1024


class ChartConfig(BaseModel):
    """Default chart rendering configuration.

    Attributes:
        default_renderer: Chart rendering backend name.
        default_format: Output image format.
        default_dpi: Dots per inch for rendering.
        default_width: Default chart width in pixels.
        default_height: Default chart height in pixels.
        matplotlib_backend: Matplotlib backend for deterministic rendering.
    """

    default_renderer: str = "matplotlib"
    default_format: str = "png"
    default_dpi: int = 150
    default_width: int = 800
    default_height: int = 600
    matplotlib_backend: str = "Agg"


class LoggingConfig(BaseModel):
    """Logging configuration.

    Attributes:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format: Log output format (``text`` or ``json``).
        log_file: Optional path to a log file.
        log_ai_interactions: Whether to log Claude prompts and responses.
    """

    level: str = "INFO"
    format: str = "text"
    log_file: Path | None = None
    log_ai_interactions: bool = False


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """Settings source that reads from pre-loaded YAML configuration data.

    This source is inserted into the pydantic-settings source chain
    with lower priority than environment variables but higher than
    field defaults.
    """

    def __init__(  # noqa: D107
        self,
        settings_cls: type[BaseSettings],
        yaml_data: dict[str, Any],
    ) -> None:
        super().__init__(settings_cls)
        self._yaml_data = yaml_data

    def get_field_value(
        self,
        field: FieldInfo,  # noqa: ARG002
        field_name: str,
    ) -> tuple[Any, str, bool]:
        """Return the value for a field from YAML data."""
        val = self._yaml_data.get(field_name)
        return val, field_name, False

    def __call__(self) -> dict[str, Any]:
        """Return all YAML configuration values."""
        return dict(self._yaml_data)


class AppConfig(BaseSettings):
    """Root application configuration.

    Load priority (highest to lowest):
        1. CLI overrides (passed as ``overrides`` to ``load_config``)
        2. Environment variables (``PYGRAMATTIC_*``)
        3. YAML config files (``configs/default.yaml``, ``configs/{env}.yaml``)
        4. Field defaults (defined here)

    Attributes:
        environment: Deployment environment name.
        storage: Storage subsystem configuration.
        database: Database connection configuration.
        claude: Claude CLI integration configuration.
        charts: Chart rendering configuration.
        logging: Logging configuration.
        templates_dir: Path to template files.
        themes_dir: Path to theme files.
        configs_dir: Path to configuration files.
    """

    model_config = SettingsConfigDict(
        env_prefix="PYGRAMATTIC_",
        env_nested_delimiter="__",
    )

    _yaml_data: ClassVar[dict[str, Any]] = {}

    environment: str = "development"
    storage: StorageConfig = StorageConfig()
    database: DatabaseConfig = DatabaseConfig()
    claude: ClaudeConfig = ClaudeConfig()
    charts: ChartConfig = ChartConfig()
    logging: LoggingConfig = LoggingConfig()
    templates_dir: Path = Path("sample_templates")
    themes_dir: Path = Path("sample_themes")
    configs_dir: Path = Path("configs")

    @classmethod
    def configure_yaml_data(cls, data: dict[str, Any]) -> None:
        """Set YAML configuration data for the custom settings source.

        Must be called before constructing an ``AppConfig`` instance
        so the YAML source has data to provide.

        Args:
            data: Merged YAML configuration dictionary.
        """
        cls._yaml_data = data

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
        **kwargs: Any,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customise settings sources for correct override priority.

        Returns sources in priority order: init (CLI overrides),
        then env vars, then YAML file values.
        """
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls, cls._yaml_data),
        )
