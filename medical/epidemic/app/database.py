"""SQLCipher/SQLite database setup for epidemic surveillance.

Production uses SQLCipher (pysqlcipher3) for encryption at rest.
Falls back to standard sqlite3 for testing and development.
"""

import sqlite3
from pathlib import Path
from typing import Any


_db_path: str = ":memory:"
_db_key: str = ""

try:
    from pysqlcipher3 import dbapi2 as sqlcipher
    _USE_SQLCIPHER = True
except ImportError:
    _USE_SQLCIPHER = False


def set_db_path(path: str, key: str = "") -> None:
    """Set the database file path and encryption key."""
    global _db_path, _db_key
    _db_path = path
    _db_key = key
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Get a database connection with optional SQLCipher encryption."""
    if _USE_SQLCIPHER and _db_key:
        conn = sqlcipher.connect(_db_path)
        conn.execute(f"PRAGMA key='{_db_key}'")
    elif _db_path == ":memory:":
        conn = sqlite3.connect("file::memory:?cache=shared", uri=True)
    else:
        conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Initialize database schema."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS symptom_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            syndrome TEXT NOT NULL,
            patient_id TEXT,
            age_group TEXT NOT NULL,
            sex TEXT NOT NULL,
            area TEXT NOT NULL DEFAULT 'default',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_symptom_date_syndrome
            ON symptom_reports(date, syndrome);
        CREATE INDEX IF NOT EXISTS idx_symptom_area
            ON symptom_reports(area);

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            syndrome TEXT NOT NULL,
            level TEXT NOT NULL,
            count INTEGER NOT NULL,
            baseline REAL NOT NULL,
            multiplier REAL NOT NULL,
            area TEXT NOT NULL,
            recommendation TEXT NOT NULL DEFAULT '',
            acknowledged INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            contact_person TEXT NOT NULL,
            relationship TEXT NOT NULL DEFAULT '',
            date_of_contact TEXT NOT NULL,
            exposure_type TEXT NOT NULL DEFAULT 'casual',
            follow_up_status TEXT NOT NULL DEFAULT 'pending',
            risk_score REAL NOT NULL DEFAULT 0.0,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (case_id) REFERENCES symptom_reports(id)
        );

        CREATE INDEX IF NOT EXISTS idx_contacts_case
            ON contacts(case_id);

        CREATE TABLE IF NOT EXISTS quarantines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person TEXT NOT NULL,
            start_date TEXT NOT NULL,
            expected_end TEXT NOT NULL,
            location TEXT NOT NULL DEFAULT '',
            reason TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS quarantine_checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quarantine_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            temperature REAL,
            symptoms TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (quarantine_id) REFERENCES quarantines(id)
        );

        CREATE TABLE IF NOT EXISTS quarantine_supplies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quarantine_id INTEGER NOT NULL,
            item TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'needed',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (quarantine_id) REFERENCES quarantines(id)
        );

        CREATE TABLE IF NOT EXISTS epidemic_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            pathogen TEXT NOT NULL DEFAULT 'unknown',
            start_date TEXT NOT NULL,
            end_date TEXT,
            total_cases INTEGER NOT NULL DEFAULT 0,
            total_deaths INTEGER NOT NULL DEFAULT 0,
            response_actions TEXT NOT NULL DEFAULT '',
            lessons_learned TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS community_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            community_id TEXT NOT NULL,
            date TEXT NOT NULL,
            syndrome TEXT NOT NULL,
            age_group TEXT NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            received_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_community_data
            ON community_data(community_id, date, syndrome);
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
