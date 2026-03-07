"""SURVIVE OS module template - replace MODULE_NAME with your module."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI
from fastapi.responses import JSONResponse

MODULE_NAME = "MODULE_NAME"
VERSION = "0.1.0"
CONFIG_PATH = Path(f"/etc/survive/{MODULE_NAME}.yml")
DATA_DIR = Path(f"/var/lib/survive/{MODULE_NAME}")


def load_config() -> dict[str, Any]:
    """Load module configuration from YAML file."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


def get_db() -> sqlite3.Connection:
    """Get a connection to the module's SQLite database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db_path = DATA_DIR / f"{MODULE_NAME}.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


config = load_config()
app = FastAPI(title=f"SURVIVE OS - {MODULE_NAME}", version=VERSION)


@app.get("/health")
async def health() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({"status": "healthy", "version": VERSION})
