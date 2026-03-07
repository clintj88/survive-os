"""SQLite database setup and access for the ham radio module."""

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
        CREATE TABLE IF NOT EXISTS winlink_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound')),
            from_addr TEXT NOT NULL,
            to_addr TEXT NOT NULL,
            subject TEXT NOT NULL DEFAULT '',
            body TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            sent_at TEXT
        );

        CREATE TABLE IF NOT EXISTS js8call_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound')),
            from_call TEXT NOT NULL DEFAULT '',
            to_call TEXT NOT NULL DEFAULT '',
            message TEXT NOT NULL DEFAULT '',
            freq INTEGER NOT NULL DEFAULT 0,
            snr INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS frequencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            freq_mhz REAL NOT NULL,
            name TEXT NOT NULL,
            band TEXT NOT NULL,
            mode TEXT NOT NULL,
            usage TEXT NOT NULL DEFAULT 'general',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS scheduled_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            callsign TEXT NOT NULL DEFAULT '',
            freq_mhz REAL,
            mode TEXT NOT NULL DEFAULT '',
            scheduled_at TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL DEFAULT 30,
            notes TEXT NOT NULL DEFAULT '',
            recurring TEXT NOT NULL DEFAULT 'none',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
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
