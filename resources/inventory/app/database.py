"""SQLite database setup and access for the inventory module."""

import sqlite3
from pathlib import Path
from typing import Any


_db_path: str = ":memory:"

VALID_CATEGORIES = (
    "food",
    "water",
    "medical",
    "tools",
    "fuel",
    "ammunition",
    "building_materials",
    "trade_goods",
)

VALID_CONDITIONS = ("new", "good", "fair", "poor")
VALID_UNITS = ("kg", "liters", "count", "gallons", "lbs", "meters", "boxes", "bags", "cans", "bottles")
VALID_LOCATION_TYPES = ("warehouse", "cache", "vehicle", "building")
VALID_ACTIONS = ("add", "remove", "transfer", "adjust", "consume", "create", "update", "delete")


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
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT NOT NULL DEFAULT '',
            quantity REAL NOT NULL DEFAULT 0,
            unit TEXT NOT NULL DEFAULT 'count',
            expiration_date TEXT,
            condition TEXT NOT NULL DEFAULT 'good',
            notes TEXT NOT NULL DEFAULT '',
            location_id INTEGER,
            qr_code TEXT UNIQUE,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (location_id) REFERENCES locations(id)
        );

        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL DEFAULT 'warehouse',
            description TEXT NOT NULL DEFAULT '',
            capacity INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS consumption_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            quantity_consumed REAL NOT NULL,
            date TEXT NOT NULL DEFAULT (datetime('now')),
            consumed_by TEXT NOT NULL DEFAULT '',
            purpose TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (item_id) REFERENCES items(id)
        );

        CREATE TABLE IF NOT EXISTS alert_thresholds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            category TEXT,
            min_level REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (item_id) REFERENCES items(id)
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            action TEXT NOT NULL,
            quantity_change REAL,
            previous_quantity REAL,
            new_quantity REAL,
            performed_by TEXT NOT NULL DEFAULT '',
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            notes TEXT NOT NULL DEFAULT ''
        );

        CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);
        CREATE INDEX IF NOT EXISTS idx_items_location ON items(location_id);
        CREATE INDEX IF NOT EXISTS idx_items_qr ON items(qr_code);
        CREATE INDEX IF NOT EXISTS idx_consumption_item ON consumption_events(item_id);
        CREATE INDEX IF NOT EXISTS idx_consumption_date ON consumption_events(date);
        CREATE INDEX IF NOT EXISTS idx_audit_item ON audit_log(item_id);
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
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


def execute_many(sql: str, params_list: list[tuple[Any, ...]]) -> None:
    conn = get_connection()
    try:
        conn.executemany(sql, params_list)
        conn.commit()
    finally:
        conn.close()
