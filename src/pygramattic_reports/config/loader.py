"""Configuration loader for pygramattic-reports.

Handles loading YAML config files, merging environment-specific
overrides, and producing a validated ``AppConfig`` instance.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from pygramattic_reports.exceptions import ConfigError

from .settings import AppConfig


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base*.

    Override values win for scalar keys. Nested dicts are merged
    recursively rather than replaced wholesale.

    Args:
        base: Base configuration dictionary.
        override: Override dictionary whose values take precedence.

    Returns:
        A new merged dictionary.
    """
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_yaml_file(path: Path) -> dict[str, Any]:
    """Load a single YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML as a dictionary, or empty dict if the file
        does not exist or contains no mapping.

    Raises:
        ConfigError: If the file exists but contains invalid YAML.
    """
    if not path.is_file():
        return {}
    try:
        with path.open() as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        msg = f"Invalid YAML in {path}: {exc}"
        raise ConfigError(msg) from exc
    if not isinstance(data, dict):
        return {}
    return data


def load_config(
    config_dir: Path | None = None,
    environment: str | None = None,
    overrides: dict[str, Any] | None = None,
) -> AppConfig:
    """Load and merge configuration from all sources.

    The final ``AppConfig`` is assembled with the following priority
    (highest to lowest):

    1. *overrides* (CLI flags)
    2. Environment variables (``PYGRAMATTIC_*``)
    3. Environment-specific YAML (``configs/{environment}.yaml``)
    4. Default YAML (``configs/default.yaml``)
    5. Field defaults

    Args:
        config_dir: Path to the configs directory.
            Defaults to ``./configs/``.
        environment: Environment name (e.g. ``"development"``,
            ``"production"``).  Defaults to the
            ``PYGRAMATTIC_ENVIRONMENT`` env var or ``"development"``.
        overrides: Additional key-value overrides applied with
            highest priority (typically from CLI flags).

    Returns:
        A fully resolved and validated ``AppConfig``.

    Raises:
        ConfigError: If YAML files are malformed or the resulting
            configuration fails validation.
    """
    config_dir = config_dir or Path("configs")
    environment = environment or os.environ.get("PYGRAMATTIC_ENVIRONMENT", "development")

    # Load and merge YAML files
    base_yaml = _load_yaml_file(config_dir / "default.yaml")
    env_yaml = _load_yaml_file(config_dir / f"{environment}.yaml")
    yaml_data = deep_merge(base_yaml, env_yaml) if env_yaml else base_yaml

    # Set YAML data for the custom settings source
    AppConfig.configure_yaml_data(yaml_data)

    # Create config with correct priority:
    #   overrides (init) > env vars > yaml > field defaults
    try:
        return AppConfig(**(overrides or {}))
    except ValidationError as exc:
        msg = f"Invalid configuration: {exc}"
        raise ConfigError(msg) from exc
