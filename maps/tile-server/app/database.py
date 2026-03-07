"""SQLite database setup and access for the tile-server module."""

import sqlite3
from pathlib import Path
from typing import Any


_db_path: str = ":memory:"

VALID_FORMATS = ("pbf", "png", "jpg", "webp")


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
        CREATE TABLE IF NOT EXISTS tilesets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            filepath TEXT NOT NULL,
            format TEXT NOT NULL DEFAULT 'pbf',
            description TEXT NOT NULL DEFAULT '',
            min_zoom INTEGER NOT NULL DEFAULT 0,
            max_zoom INTEGER NOT NULL DEFAULT 14,
            bounds TEXT NOT NULL DEFAULT '-180,-85.0511,180,85.0511',
            center_lat REAL NOT NULL DEFAULT 0.0,
            center_lng REAL NOT NULL DEFAULT 0.0,
            center_zoom INTEGER NOT NULL DEFAULT 2,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_tilesets_name ON tilesets(name);
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
