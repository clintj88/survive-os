"""SQLite database setup and access for the engineering module."""

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
        CREATE TABLE IF NOT EXISTS infrastructure_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL CHECK(category IN ('water','power','building','vehicle','equipment')),
            location TEXT NOT NULL DEFAULT '',
            install_date TEXT,
            condition TEXT NOT NULL DEFAULT 'good' CHECK(condition IN ('good','fair','poor','critical')),
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS maintenance_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            task_description TEXT NOT NULL,
            frequency_days INTEGER NOT NULL,
            last_performed TEXT,
            next_due TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES infrastructure_items(id)
        );

        CREATE TABLE IF NOT EXISTS maintenance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            performed_at TEXT NOT NULL DEFAULT (datetime('now')),
            performed_by TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (schedule_id) REFERENCES maintenance_schedules(id),
            FOREIGN KEY (item_id) REFERENCES infrastructure_items(id)
        );

        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_number TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            fits_equipment TEXT NOT NULL DEFAULT '[]',
            salvage_sources TEXT NOT NULL DEFAULT '[]',
            quantity_on_hand INTEGER NOT NULL DEFAULT 0,
            location TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS chemistry_recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            ingredients TEXT NOT NULL DEFAULT '[]',
            procedure TEXT NOT NULL DEFAULT '[]',
            safety_notes TEXT NOT NULL DEFAULT '',
            yield TEXT NOT NULL DEFAULT '',
            difficulty TEXT NOT NULL DEFAULT 'medium' CHECK(difficulty IN ('easy','medium','hard'))
        );

        CREATE TABLE IF NOT EXISTS technical_guides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            parts_needed TEXT NOT NULL DEFAULT '[]',
            difficulty TEXT NOT NULL DEFAULT 'medium',
            author TEXT NOT NULL DEFAULT 'system',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS technical_drawings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            file_path TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT '',
            related_equipment TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
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
