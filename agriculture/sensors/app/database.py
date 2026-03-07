"""SQLite database setup and access for the sensor module."""

import sqlite3
from pathlib import Path
from typing import Any


_db_path: str = ":memory:"


def set_db_path(path: str) -> None:
    """Set the database file path."""
    global _db_path
    _db_path = path
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory enabled."""
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Initialize database schema with time-series indexing."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS nodes (
            node_id TEXT PRIMARY KEY,
            name TEXT NOT NULL DEFAULT '',
            location TEXT NOT NULL DEFAULT '',
            type TEXT NOT NULL DEFAULT 'unknown',
            last_seen TEXT,
            battery_level REAL,
            firmware_version TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'offline',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS soil_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            moisture_pct REAL NOT NULL,
            depth_cm REAL,
            temperature_c REAL,
            timestamp TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (node_id) REFERENCES nodes(node_id)
        );
        CREATE INDEX IF NOT EXISTS idx_soil_ts ON soil_readings(timestamp);
        CREATE INDEX IF NOT EXISTS idx_soil_node ON soil_readings(node_id, timestamp);

        CREATE TABLE IF NOT EXISTS weather_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            temperature_c REAL,
            humidity_pct REAL,
            pressure_hpa REAL,
            timestamp TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (node_id) REFERENCES nodes(node_id)
        );
        CREATE INDEX IF NOT EXISTS idx_weather_ts ON weather_readings(timestamp);
        CREATE INDEX IF NOT EXISTS idx_weather_node ON weather_readings(node_id, timestamp);

        CREATE TABLE IF NOT EXISTS rain_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            rainfall_mm REAL NOT NULL,
            period_minutes INTEGER,
            timestamp TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (node_id) REFERENCES nodes(node_id)
        );
        CREATE INDEX IF NOT EXISTS idx_rain_ts ON rain_readings(timestamp);
        CREATE INDEX IF NOT EXISTS idx_rain_node ON rain_readings(node_id, timestamp);

        CREATE TABLE IF NOT EXISTS frost_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            location TEXT NOT NULL DEFAULT '',
            temperature_c REAL NOT NULL,
            trend TEXT NOT NULL DEFAULT 'unknown',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (node_id) REFERENCES nodes(node_id)
        );
        CREATE INDEX IF NOT EXISTS idx_frost_ts ON frost_alerts(created_at);
    """)
    conn.commit()
    conn.close()


def query(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    """Execute a query and return results as list of dicts."""
    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    """Execute a statement and return the lastrowid."""
    conn = get_connection()
    try:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.lastrowid or 0
    finally:
        conn.close()


def execute_many(sql: str, params_list: list[tuple[Any, ...]]) -> None:
    """Execute a statement with multiple parameter sets."""
    conn = get_connection()
    try:
        conn.executemany(sql, params_list)
        conn.commit()
    finally:
        conn.close()
