"""Configuration loader for the pharmacy module."""

from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG: dict[str, Any] = {
    "database": {
        "path": "/var/lib/survive/pharmacy/pharmacy.db",
        "key": "change-me-in-production",
    },
    "server": {
        "host": "0.0.0.0",
        "port": 8040,
    },
    "alerts": {
        "thresholds_days": [30, 60, 90],
    },
    "redis": {
        "host": "localhost",
        "port": 6379,
        "channel": "medical.pharmacy-alerts",
    },
    "lldap": {
        "url": "ldap://localhost:3890",
    },
    "version": "0.1.0",
}

CONFIG_PATH = Path("/etc/survive/pharmacy.yml")


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
