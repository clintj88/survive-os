"""Configuration loader for the medical specialty module."""

from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG: dict[str, Any] = {
    "database": {
        "path": "/var/lib/survive/medical-specialty/specialty.db",
        "key": "survive-medical-specialty-default-key",
    },
    "server": {
        "host": "0.0.0.0",
        "port": 8040,
    },
    "lldap": {
        "url": "ldap://localhost:3890",
    },
    "agriculture_api": {
        "url": "http://localhost:8030",
    },
    "version": "0.1.0",
}

CONFIG_PATH = Path("/etc/survive/medical-specialty.yml")


def load_config() -> dict[str, Any]:
    """Load configuration from YAML file, falling back to defaults."""
    config = DEFAULT_CONFIG.copy()
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            user_config = yaml.safe_load(f) or {}
        _deep_merge(config, user_config)
    return config


def _deep_merge(base: dict, override: dict) -> None:
    """Merge override dict into base dict recursively."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
