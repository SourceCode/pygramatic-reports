"""Configuration management for pygramattic-reports.

Usage::

    from pygramattic_reports.config import load_config

    config = load_config()
    print(config.storage.data_dir)
"""

from pygramattic_reports.exceptions import ConfigError

from .loader import load_config
from .settings import AppConfig

__all__ = ["AppConfig", "ConfigError", "load_config"]
