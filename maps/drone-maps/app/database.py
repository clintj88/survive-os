"""SQLite database setup and access for the drone-maps module."""

import sqlite3
from pathlib import Path
from typing import Any


_db_path: str = ":memory:"

VALID_SURVEY_STATUSES = ("planned", "in_progress", "completed")
VALID_JOB_STATUSES = ("pending", "processing", "completed", "failed")
VALID_CHANGE_TYPES = ("new_construction", "crop_changes", "erosion", "water_level", "other")
VALID_SEVERITIES = ("low", "medium", "high")


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
        CREATE TABLE IF NOT EXISTS surveys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            area_name TEXT NOT NULL DEFAULT '',
            date TEXT NOT NULL DEFAULT (date('now')),
            drone_model TEXT NOT NULL DEFAULT '',
            operator TEXT NOT NULL DEFAULT '',
            bounds TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'planned',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            survey_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL DEFAULT '',
            latitude REAL,
            longitude REAL,
            altitude REAL,
            captured_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (survey_id) REFERENCES surveys(id)
        );

        CREATE TABLE IF NOT EXISTS processing_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            survey_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            output_path TEXT NOT NULL DEFAULT '',
            resolution REAL,
            file_size INTEGER,
            started_at TEXT,
            completed_at TEXT,
            error_message TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (survey_id) REFERENCES surveys(id)
        );

        CREATE TABLE IF NOT EXISTS change_detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            survey_a_id INTEGER NOT NULL,
            survey_b_id INTEGER NOT NULL,
            change_type TEXT NOT NULL,
            geometry TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            severity TEXT NOT NULL DEFAULT 'low',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (survey_a_id) REFERENCES surveys(id),
            FOREIGN KEY (survey_b_id) REFERENCES surveys(id)
        );

        CREATE TABLE IF NOT EXISTS terrain_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            survey_id INTEGER NOT NULL,
            filepath TEXT NOT NULL,
            resolution REAL,
            bounds TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (survey_id) REFERENCES surveys(id)
        );

        CREATE INDEX IF NOT EXISTS idx_images_survey ON images(survey_id);
        CREATE INDEX IF NOT EXISTS idx_jobs_survey ON processing_jobs(survey_id);
        CREATE INDEX IF NOT EXISTS idx_jobs_status ON processing_jobs(status);
        CREATE INDEX IF NOT EXISTS idx_changes_survey_a ON change_detections(survey_a_id);
        CREATE INDEX IF NOT EXISTS idx_changes_survey_b ON change_detections(survey_b_id);
        CREATE INDEX IF NOT EXISTS idx_terrain_survey ON terrain_models(survey_id);
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
