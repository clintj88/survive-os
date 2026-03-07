"""SQLite database setup and access for the weather module."""

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
    """Initialize database schema."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            observed_at TEXT NOT NULL,
            observer TEXT NOT NULL DEFAULT 'system',
            source TEXT NOT NULL DEFAULT 'manual',
            temperature_c REAL,
            humidity_pct REAL,
            pressure_hpa REAL,
            pressure_feel TEXT,
            wind_speed_kph REAL,
            wind_direction TEXT,
            cloud_type TEXT,
            precipitation TEXT DEFAULT 'none',
            precipitation_type TEXT,
            visibility TEXT DEFAULT 'good',
            rainfall_mm REAL DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_observations_at
            ON observations(observed_at);
        CREATE INDEX IF NOT EXISTS idx_observations_source
            ON observations(source);

        CREATE TABLE IF NOT EXISTS forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            generated_at TEXT NOT NULL DEFAULT (datetime('now')),
            valid_from TEXT NOT NULL,
            valid_to TEXT NOT NULL,
            summary TEXT NOT NULL,
            temperature_high_c REAL,
            temperature_low_c REAL,
            precipitation_chance_pct REAL,
            wind_forecast TEXT,
            confidence_pct REAL DEFAULT 50,
            method TEXT DEFAULT 'pattern_match'
        );

        CREATE TABLE IF NOT EXISTS storm_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            detected_at TEXT NOT NULL DEFAULT (datetime('now')),
            ended_at TEXT,
            severity TEXT NOT NULL DEFAULT 'watch',
            event_type TEXT NOT NULL,
            description TEXT NOT NULL,
            max_wind_kph REAL,
            total_precipitation_mm REAL DEFAULT 0,
            pressure_drop_hpa REAL,
            active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS frost_dates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            frost_type TEXT NOT NULL,
            frost_date TEXT NOT NULL,
            UNIQUE(year, frost_type)
        );

        CREATE TABLE IF NOT EXISTS planting_advisories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            advisory_type TEXT NOT NULL,
            message TEXT NOT NULL,
            valid_from TEXT,
            valid_to TEXT
        );
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
