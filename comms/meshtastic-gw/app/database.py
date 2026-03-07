"""SQLite database setup and access for the Meshtastic gateway."""

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
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL DEFAULT '',
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            channel INTEGER NOT NULL DEFAULT 0,
            mesh_id TEXT NOT NULL DEFAULT '',
            direction TEXT NOT NULL DEFAULT 'rx',
            ack INTEGER NOT NULL DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_messages_timestamp
            ON messages(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_messages_sender
            ON messages(sender);
        CREATE INDEX IF NOT EXISTS idx_messages_channel
            ON messages(channel);

        CREATE TABLE IF NOT EXISTS radios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL UNIQUE,
            long_name TEXT NOT NULL DEFAULT '',
            short_name TEXT NOT NULL DEFAULT '',
            hw_model TEXT NOT NULL DEFAULT '',
            assigned_user TEXT NOT NULL DEFAULT '',
            connection_type TEXT NOT NULL DEFAULT 'serial',
            connection_address TEXT NOT NULL DEFAULT '',
            battery_level INTEGER NOT NULL DEFAULT 0,
            snr REAL NOT NULL DEFAULT 0,
            last_seen TEXT NOT NULL DEFAULT (datetime('now')),
            latitude REAL,
            longitude REAL,
            altitude REAL
        );

        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL DEFAULT '',
            role TEXT NOT NULL DEFAULT 'SECONDARY',
            psk TEXT NOT NULL DEFAULT ''
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
