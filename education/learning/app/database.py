"""SQLite database setup and access for the learning module."""

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
        CREATE TABLE IF NOT EXISTS apprentices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_name TEXT NOT NULL,
            trade TEXT NOT NULL,
            mentor_name TEXT NOT NULL DEFAULT '',
            start_date TEXT NOT NULL DEFAULT (date('now')),
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','completed','paused')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS skill_checklists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade TEXT NOT NULL,
            skill_name TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS apprentice_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            apprentice_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'not_started' CHECK(status IN ('not_started','in_progress','demonstrated','certified')),
            certified_date TEXT,
            certified_by TEXT,
            FOREIGN KEY (apprentice_id) REFERENCES apprentices(id),
            FOREIGN KEY (skill_id) REFERENCES skill_checklists(id),
            UNIQUE(apprentice_id, skill_id)
        );

        CREATE TABLE IF NOT EXISTS lesson_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            age_group TEXT NOT NULL DEFAULT 'adult' CHECK(age_group IN ('children','teen','adult')),
            duration TEXT NOT NULL DEFAULT '',
            objectives TEXT NOT NULL DEFAULT '[]',
            materials_needed TEXT NOT NULL DEFAULT '[]',
            procedure TEXT NOT NULL DEFAULT '[]',
            assessment TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS curricula (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            grade_level TEXT NOT NULL DEFAULT '',
            topic_sequence TEXT NOT NULL DEFAULT '[]',
            recommended_resources TEXT NOT NULL DEFAULT '[]'
        );

        CREATE TABLE IF NOT EXISTS children_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_name TEXT NOT NULL,
            exercise_type TEXT NOT NULL,
            difficulty INTEGER NOT NULL DEFAULT 1,
            score INTEGER NOT NULL DEFAULT 0,
            total INTEGER NOT NULL DEFAULT 0,
            completed_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS reading_passages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            difficulty INTEGER NOT NULL DEFAULT 1,
            passage TEXT NOT NULL,
            questions TEXT NOT NULL DEFAULT '[]'
        );

        CREATE TABLE IF NOT EXISTS science_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            difficulty INTEGER NOT NULL DEFAULT 1,
            description TEXT NOT NULL DEFAULT '',
            materials TEXT NOT NULL DEFAULT '[]',
            steps TEXT NOT NULL DEFAULT '[]'
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
