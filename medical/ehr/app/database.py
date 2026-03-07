"""SQLite/SQLCipher database setup and access for EHR.

Production uses pysqlcipher3 for encryption at rest.
Falls back to standard sqlite3 for development/testing.
"""

import sqlite3
from pathlib import Path
from typing import Any


_db_path: str = ":memory:"
_db_key: str = ""

# Try to use SQLCipher; fall back to plain sqlite3
try:
    from pysqlcipher3 import dbapi2 as sqlcipher  # type: ignore[import-untyped]
    _HAS_SQLCIPHER = True
except ImportError:
    _HAS_SQLCIPHER = False


def set_db_path(path: str, key: str = "") -> None:
    """Set the database file path and encryption key."""
    global _db_path, _db_key
    _db_path = path
    _db_key = key
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Get a database connection with optional SQLCipher encryption."""
    if _HAS_SQLCIPHER and _db_key:
        conn = sqlcipher.connect(_db_path)
        conn.execute(f"PRAGMA key='{_db_key}'")
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
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            sex TEXT NOT NULL CHECK (sex IN ('M', 'F', 'Other')),
            blood_type TEXT DEFAULT '',
            allergies TEXT NOT NULL DEFAULT '[]',
            chronic_conditions TEXT NOT NULL DEFAULT '[]',
            emergency_contact TEXT DEFAULT '',
            photo_path TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            visit_date TEXT NOT NULL DEFAULT (datetime('now')),
            provider TEXT NOT NULL,
            subjective TEXT DEFAULT '',
            objective TEXT DEFAULT '',
            assessment TEXT DEFAULT '',
            plan TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );

        CREATE TABLE IF NOT EXISTS vitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            visit_id INTEGER,
            recorded_at TEXT NOT NULL DEFAULT (datetime('now')),
            temperature REAL,
            pulse INTEGER,
            bp_systolic INTEGER,
            bp_diastolic INTEGER,
            respiration_rate INTEGER,
            spo2 REAL,
            weight REAL,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (visit_id) REFERENCES visits(id)
        );

        CREATE TABLE IF NOT EXISTS wounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            body_location TEXT NOT NULL,
            wound_type TEXT NOT NULL,
            size TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );

        CREATE TABLE IF NOT EXISTS wound_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wound_id INTEGER NOT NULL,
            entry_date TEXT NOT NULL DEFAULT (datetime('now')),
            treatment_notes TEXT DEFAULT '',
            photo_path TEXT DEFAULT '',
            healing_status TEXT DEFAULT 'ongoing',
            FOREIGN KEY (wound_id) REFERENCES wounds(id)
        );

        CREATE TABLE IF NOT EXISTS vaccinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            vaccine_name TEXT NOT NULL,
            date_administered TEXT NOT NULL,
            lot_number TEXT DEFAULT '',
            site TEXT DEFAULT '',
            administered_by TEXT DEFAULT '',
            next_dose_due TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            user_name TEXT NOT NULL,
            action TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id TEXT,
            details TEXT DEFAULT ''
        );

        CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(last_name, first_name);
        CREATE INDEX IF NOT EXISTS idx_patients_dob ON patients(date_of_birth);
        CREATE INDEX IF NOT EXISTS idx_visits_patient ON visits(patient_id);
        CREATE INDEX IF NOT EXISTS idx_vitals_patient ON vitals(patient_id);
        CREATE INDEX IF NOT EXISTS idx_wounds_patient ON wounds(patient_id);
        CREATE INDEX IF NOT EXISTS idx_wound_entries_wound ON wound_entries(wound_id);
        CREATE INDEX IF NOT EXISTS idx_vaccinations_patient ON vaccinations(patient_id);
        CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
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
