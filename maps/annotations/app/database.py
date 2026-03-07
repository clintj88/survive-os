"""SQLite database setup and access for the map annotations module."""

import sqlite3
from pathlib import Path
from typing import Any


_db_path: str = ":memory:"

VALID_LAYER_TYPES = (
    "resource_locations",
    "hazard_zones",
    "agricultural_plots",
    "patrol_routes",
    "trade_routes",
    "mesh_nodes",
)

VALID_CATEGORIES = (
    "water_source",
    "fuel_cache",
    "supply_depot",
    "contamination",
    "structural_collapse",
    "flooding",
    "crop_assignment",
    "patrol_route",
    "checkpoint",
    "trade_route",
    "travel_corridor",
    "meshtastic_node",
)


def set_db_path(path: str) -> None:
    global _db_path
    _db_path = path
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS layers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            color TEXT NOT NULL DEFAULT '#4facfe',
            visible INTEGER NOT NULL DEFAULT 1,
            description TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS annotations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            layer_id INTEGER NOT NULL,
            geometry TEXT NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            properties TEXT NOT NULL DEFAULT '{}',
            creator TEXT NOT NULL DEFAULT '',
            crdt_id TEXT UNIQUE,
            radius_meters REAL,
            latitude REAL,
            longitude REAL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (layer_id) REFERENCES layers(id)
        );

        CREATE INDEX IF NOT EXISTS idx_annotations_layer ON annotations(layer_id);
        CREATE INDEX IF NOT EXISTS idx_annotations_category ON annotations(category);
        CREATE INDEX IF NOT EXISTS idx_annotations_crdt ON annotations(crdt_id);
        CREATE INDEX IF NOT EXISTS idx_annotations_lat ON annotations(latitude);
        CREATE INDEX IF NOT EXISTS idx_annotations_lng ON annotations(longitude);
    """)
    conn.commit()
    conn.close()


def query(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.lastrowid or 0
    finally:
        conn.close()
