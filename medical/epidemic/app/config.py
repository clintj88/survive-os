"""Configuration loader for the epidemic surveillance module."""

from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG: dict[str, Any] = {
    "database": {
        "path": "/var/lib/survive/epidemic/epidemic.db",
        "key": "changeme-epidemic-key",
    },
    "server": {
        "host": "0.0.0.0",
        "port": 8040,
    },
    "surveillance": {
        "baseline_window_weeks": 4,
        "alert_thresholds": {
            "watch": 1.5,
            "warning": 2.0,
            "critical": 3.0,
        },
    },
    "redis": {
        "url": "redis://localhost:6379",
    },
    "version": "0.1.0",
}

CONFIG_PATH = Path("/etc/survive/epidemic.yml")


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
