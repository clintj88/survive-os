"""Configuration loader for the sync engine."""

from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG: dict[str, Any] = {
    "database": {
        "path": "/var/lib/survive/sync/sync.db",
    },
    "storage": {
        "path": "/var/lib/survive/sync/documents",
    },
    "server": {
        "host": "0.0.0.0",
        "port": 8100,
    },
    "version": "0.1.0",
    "node": {
        "id": "",
        "name": "",
        "role": "spoke",
        "community": "default",
    },
    "sync": {
        "interval_seconds": 30,
        "batch_size": 50,
        "max_document_size_bytes": 10485760,
        "retry_max": 5,
        "retry_backoff_seconds": 5,
    },
    "transport": {
        "tcp": {
            "enabled": True,
            "port": 8101,
            "mdns_name": "_survive-sync._tcp.local.",
        },
        "redis": {
            "enabled": True,
            "url": "redis://localhost:6379",
            "channel_prefix": "survive:sync:",
        },
        "serial": {
            "enabled": False,
            "device": "/dev/ttyUSB0",
            "baud_rate": 9600,
            "chunk_size": 256,
        },
    },
    "discovery": {
        "mdns_enabled": True,
        "static_peers": [],
    },
}

CONFIG_PATH = Path("/etc/survive/sync.yml")


def load_config() -> dict[str, Any]:
    """Load configuration from YAML file, falling back to defaults."""
    config = DEFAULT_CONFIG.copy()
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            user_config = yaml.safe_load(f) or {}
        _deep_merge(config, user_config)
    return config


def _deep_merge(base: dict, override: dict) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
