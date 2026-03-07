"""Configuration loader for the seed bank module."""

from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG: dict[str, Any] = {
    "database": {
        "path": "/var/lib/survive/seed-bank/seed-bank.db",
    },
    "server": {
        "host": "0.0.0.0",
        "port": 8030,
    },
    "alerts": {
        "low_stock_threshold": 50,
        "min_diversity_sources": 3,
    },
    "redis": {
        "host": "localhost",
        "port": 6379,
        "exchange_channel": "agriculture.seed-exchange",
    },
    "version": "0.1.0",
}

CONFIG_PATH = Path("/etc/survive/seed-bank.yml")


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
