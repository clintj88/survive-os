"""SQLite database setup and access for the alerts module."""

import sqlite3
from pathlib import Path
from typing import Any


_db_path: str = ":memory:"


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
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            severity TEXT NOT NULL CHECK(severity IN ('info', 'warning', 'critical', 'emergency')),
            author TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            resolved_at TEXT,
            resolved_by TEXT
        );

        CREATE TABLE IF NOT EXISTS alert_acknowledgments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            acknowledged_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (alert_id) REFERENCES alerts(id),
            UNIQUE(alert_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS alert_broadcast_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id INTEGER NOT NULL,
            channel TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'sent',
            sent_at TEXT NOT NULL DEFAULT (datetime('now')),
            error TEXT,
            FOREIGN KEY (alert_id) REFERENCES alerts(id)
        );

        CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(active);
        CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
        CREATE INDEX IF NOT EXISTS idx_ack_alert ON alert_acknowledgments(alert_id);
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
