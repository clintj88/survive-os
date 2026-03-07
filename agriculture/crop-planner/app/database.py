"""SQLite database setup and access for the crop planner."""

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
        CREATE TABLE IF NOT EXISTS fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            rows INTEGER NOT NULL DEFAULT 4,
            cols INTEGER NOT NULL DEFAULT 4,
            description TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS plots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id INTEGER NOT NULL,
            row_idx INTEGER NOT NULL,
            col_idx INTEGER NOT NULL,
            label TEXT NOT NULL DEFAULT '',
            soil_type TEXT NOT NULL DEFAULT 'loam',
            FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE,
            UNIQUE(field_id, row_idx, col_idx)
        );

        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            family TEXT NOT NULL DEFAULT '',
            rotation_group TEXT NOT NULL DEFAULT '',
            days_to_maturity INTEGER NOT NULL DEFAULT 90,
            sow_indoor_offset INTEGER,
            sow_outdoor_offset INTEGER,
            transplant_offset INTEGER,
            harvest_start_offset INTEGER,
            harvest_end_offset INTEGER,
            notes TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS plot_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plot_id INTEGER NOT NULL,
            crop_id INTEGER NOT NULL,
            season TEXT NOT NULL,
            year INTEGER NOT NULL,
            planted_at TEXT,
            harvested_at TEXT,
            notes TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (plot_id) REFERENCES plots(id) ON DELETE CASCADE,
            FOREIGN KEY (crop_id) REFERENCES crops(id),
            UNIQUE(plot_id, season, year)
        );

        CREATE TABLE IF NOT EXISTS rotation_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            climate_zone TEXT NOT NULL DEFAULT 'temperate',
            description TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS rotation_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            year_offset INTEGER NOT NULL,
            rotation_group TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (template_id) REFERENCES rotation_templates(id) ON DELETE CASCADE,
            UNIQUE(template_id, year_offset)
        );

        CREATE TABLE IF NOT EXISTS companions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_a TEXT NOT NULL,
            crop_b TEXT NOT NULL,
            relationship TEXT NOT NULL CHECK(relationship IN ('beneficial', 'neutral', 'antagonistic')),
            notes TEXT NOT NULL DEFAULT '',
            UNIQUE(crop_a, crop_b)
        );

        CREATE TABLE IF NOT EXISTS yields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plot_id INTEGER NOT NULL,
            crop_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            season TEXT NOT NULL,
            amount REAL NOT NULL,
            unit TEXT NOT NULL DEFAULT 'kg',
            notes TEXT NOT NULL DEFAULT '',
            recorded_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (plot_id) REFERENCES plots(id) ON DELETE CASCADE,
            FOREIGN KEY (crop_id) REFERENCES crops(id)
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


def execute_many(sql: str, params_list: list[tuple[Any, ...]]) -> None:
    """Execute a statement with multiple parameter sets."""
    conn = get_connection()
    try:
        conn.executemany(sql, params_list)
        conn.commit()
    finally:
        conn.close()
