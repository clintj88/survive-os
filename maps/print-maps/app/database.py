"""SQLite database setup and access for the print-maps module."""

import sqlite3
from pathlib import Path
from typing import Any


_db_path: str = ":memory:"

VALID_PAPER_SIZES = ("A4", "A3", "letter", "tabloid", "custom")
VALID_ORIENTATIONS = ("portrait", "landscape")
VALID_DPI = (150, 300, 600)
VALID_STATUSES = ("pending", "rendering", "completed", "failed")
VALID_TEMPLATE_TYPES = ("patrol_map", "foraging_map", "trade_route_map", "general")


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
        CREATE TABLE IF NOT EXISTS print_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL DEFAULT '',
            center_lat REAL NOT NULL,
            center_lng REAL NOT NULL,
            zoom INTEGER NOT NULL DEFAULT 13,
            paper_size TEXT NOT NULL DEFAULT 'A4',
            paper_width_mm REAL,
            paper_height_mm REAL,
            orientation TEXT NOT NULL DEFAULT 'portrait',
            dpi INTEGER NOT NULL DEFAULT 300,
            overlay_layers TEXT NOT NULL DEFAULT '[]',
            include_legend INTEGER NOT NULL DEFAULT 1,
            include_scale_bar INTEGER NOT NULL DEFAULT 1,
            include_north_arrow INTEGER NOT NULL DEFAULT 1,
            include_grid INTEGER NOT NULL DEFAULT 0,
            include_date INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'pending',
            output_path TEXT,
            file_size INTEGER,
            error_message TEXT,
            requested_by TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            completed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS print_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL DEFAULT '',
            template_type TEXT NOT NULL DEFAULT 'general',
            paper_size TEXT NOT NULL DEFAULT 'A4',
            orientation TEXT NOT NULL DEFAULT 'portrait',
            dpi INTEGER NOT NULL DEFAULT 300,
            overlay_layers TEXT NOT NULL DEFAULT '[]',
            include_legend INTEGER NOT NULL DEFAULT 1,
            include_scale_bar INTEGER NOT NULL DEFAULT 1,
            include_north_arrow INTEGER NOT NULL DEFAULT 1,
            include_grid INTEGER NOT NULL DEFAULT 0,
            include_date INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_jobs_status ON print_jobs(status);
        CREATE INDEX IF NOT EXISTS idx_jobs_created ON print_jobs(created_at);
        CREATE INDEX IF NOT EXISTS idx_templates_type ON print_templates(template_type);
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
