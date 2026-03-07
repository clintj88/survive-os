"""Configuration loader for the backup module."""

from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG: dict[str, Any] = {
    "version": "0.1.0",
    "server": {
        "host": "0.0.0.0",
        "port": 8002,
    },
    "backup": {
        "snapshot_dir": "/var/lib/survive/backups/snapshots",
        "archive_dir": "/var/lib/survive/backups/archives",
        "blob_dir": "/var/lib/survive/blobs",
        "status_db": "/var/lib/survive/backups/backup_status.db",
        "retention_days": 30,
    },
    "modules": {
        "bbs": {"db_path": "/var/lib/survive/bbs/bbs.db"},
        "ham-radio": {"db_path": "/var/lib/survive/ham-radio/ham-radio.db"},
        "agriculture": {"db_path": "/var/lib/survive/agriculture/agriculture.db"},
        "medical": {"db_path": "/var/lib/survive/medical/medical.db", "key": ""},
        "inventory": {"db_path": "/var/lib/survive/inventory/inventory.db"},
        "governance": {"db_path": "/var/lib/survive/governance/governance.db"},
        "maps": {"db_path": "/var/lib/survive/maps/maps.db"},
        "education": {"db_path": "/var/lib/survive/education/education.db"},
    },
    "encryption": {
        "passphrase": "",
    },
    "paper": {
        "output_dir": "/var/lib/survive/backups/paper",
        "modules": ["medical", "inventory", "agriculture"],
    },
}

CONFIG_PATH = Path("/etc/survive/backup.yml")


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load configuration from YAML file, falling back to defaults."""
    config = _deep_copy(DEFAULT_CONFIG)
    config_path = path or CONFIG_PATH
    if config_path.exists():
        with open(config_path) as f:
            user_config = yaml.safe_load(f) or {}
        _deep_merge(config, user_config)
    return config


def _deep_copy(d: dict) -> dict:
    result = {}
    for k, v in d.items():
        if isinstance(v, dict):
            result[k] = _deep_copy(v)
        elif isinstance(v, list):
            result[k] = v[:]
        else:
            result[k] = v
    return result


def _deep_merge(base: dict, override: dict) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
