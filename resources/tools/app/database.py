"""SQLite database setup and access for the tool library module."""

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
        CREATE TABLE IF NOT EXISTS tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL CHECK(category IN (
                'hand_tools','power_tools','garden','mechanical',
                'kitchen','medical','measuring','safety'
            )),
            description TEXT NOT NULL DEFAULT '',
            condition TEXT NOT NULL DEFAULT 'good' CHECK(condition IN (
                'excellent','good','fair','poor','broken'
            )),
            status TEXT NOT NULL DEFAULT 'available' CHECK(status IN (
                'available','checked_out','maintenance','retired'
            )),
            location TEXT NOT NULL DEFAULT '',
            acquired_date TEXT,
            value_estimate REAL,
            photo_path TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS checkouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_id INTEGER NOT NULL,
            borrowed_by TEXT NOT NULL,
            checkout_date TEXT NOT NULL DEFAULT (datetime('now')),
            expected_return_date TEXT NOT NULL,
            actual_return_date TEXT,
            condition_at_checkout TEXT NOT NULL,
            condition_at_return TEXT,
            notes TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (tool_id) REFERENCES tools(id)
        );

        CREATE TABLE IF NOT EXISTS maintenance_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_id INTEGER NOT NULL,
            task TEXT NOT NULL CHECK(task IN (
                'sharpen','oil','clean','calibrate','repair'
            )),
            frequency_days INTEGER NOT NULL,
            last_performed TEXT,
            next_due TEXT NOT NULL,
            FOREIGN KEY (tool_id) REFERENCES tools(id)
        );

        CREATE TABLE IF NOT EXISTS maintenance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_id INTEGER NOT NULL,
            task TEXT NOT NULL,
            performed_by TEXT NOT NULL DEFAULT '',
            performed_date TEXT NOT NULL DEFAULT (datetime('now')),
            notes TEXT NOT NULL DEFAULT '',
            parts_used TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (tool_id) REFERENCES tools(id)
        );

        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_id INTEGER NOT NULL,
            reserved_by TEXT NOT NULL,
            date_needed TEXT NOT NULL,
            duration_days INTEGER NOT NULL DEFAULT 1,
            purpose TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN (
                'active','fulfilled','cancelled'
            )),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (tool_id) REFERENCES tools(id)
        );
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
