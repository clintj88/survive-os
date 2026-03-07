"""Configuration loader for the weather module."""

from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG: dict[str, Any] = {
    "database": {
        "path": "/var/lib/survive/weather/weather.db",
    },
    "server": {
        "host": "0.0.0.0",
        "port": 8080,
    },
    "redis": {
        "url": "redis://localhost:6379",
    },
    "alerts": {
        "pressure_drop_threshold_hpa": 3.0,
        "pressure_drop_window_hours": 3,
        "high_wind_kph": 60,
        "temp_drop_threshold_c": 8.0,
        "temp_drop_window_hours": 3,
    },
    "location": {
        "name": "Community",
        "latitude": 0.0,
        "longitude": 0.0,
        "elevation_m": 0,
    },
    "frost": {
        "avg_last_spring": "04-15",
        "avg_first_fall": "10-15",
    },
    "version": "0.1.0",
}

CONFIG_PATH = Path("/etc/survive/weather.yml")


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
