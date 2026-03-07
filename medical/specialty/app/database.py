"""SQLite/SQLCipher database setup for the medical specialty module.

Production uses SQLCipher (pysqlcipher3) for encryption at rest.
Falls back to standard sqlite3 for development and testing.
"""

import sqlite3
from pathlib import Path
from typing import Any


_db_path: str = ":memory:"
_db_key: str = ""

# Try to use SQLCipher; fall back to sqlite3
try:
    from pysqlcipher3 import dbapi2 as sqlcipher  # type: ignore[import-untyped]
    _use_sqlcipher = True
except ImportError:
    _use_sqlcipher = False


def set_db_path(path: str, key: str = "") -> None:
    """Set the database file path and encryption key."""
    global _db_path, _db_key
    _db_path = path
    _db_key = key
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory enabled."""
    if _use_sqlcipher and _db_key:
        conn = sqlcipher.connect(_db_path)
        conn.execute(f"PRAGMA key='{_db_key}'")
    else:
        conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Initialize all specialty module database tables."""
    conn = get_connection()
    conn.executescript(_SCHEMA)
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


_SCHEMA = """
-- Prenatal patients
CREATE TABLE IF NOT EXISTS prenatal_patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL UNIQUE,
    estimated_due_date TEXT NOT NULL,
    gravida INTEGER NOT NULL DEFAULT 1,
    para INTEGER NOT NULL DEFAULT 0,
    risk_factors TEXT NOT NULL DEFAULT '[]',
    blood_type TEXT NOT NULL DEFAULT '',
    rh_factor TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Prenatal visits
CREATE TABLE IF NOT EXISTS prenatal_visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prenatal_patient_id INTEGER NOT NULL,
    visit_date TEXT NOT NULL,
    week_number INTEGER NOT NULL,
    fundal_height REAL,
    fetal_heart_rate REAL,
    maternal_weight REAL,
    blood_pressure TEXT,
    notes TEXT NOT NULL DEFAULT '',
    provider TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (prenatal_patient_id) REFERENCES prenatal_patients(id)
);

-- Delivery log
CREATE TABLE IF NOT EXISTS deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prenatal_patient_id INTEGER NOT NULL,
    delivery_date TEXT NOT NULL,
    delivery_type TEXT NOT NULL,
    complications TEXT NOT NULL DEFAULT '',
    birth_weight REAL,
    apgar_1min INTEGER,
    apgar_5min INTEGER,
    provider TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (prenatal_patient_id) REFERENCES prenatal_patients(id)
);

-- Postpartum follow-ups
CREATE TABLE IF NOT EXISTS postpartum_followups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prenatal_patient_id INTEGER NOT NULL,
    scheduled_date TEXT NOT NULL,
    completed_date TEXT,
    followup_type TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    provider TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (prenatal_patient_id) REFERENCES prenatal_patients(id)
);

-- Dental patients
CREATE TABLE IF NOT EXISTS dental_patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL UNIQUE,
    is_pediatric INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Tooth chart (per-tooth status)
CREATE TABLE IF NOT EXISTS tooth_chart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dental_patient_id INTEGER NOT NULL,
    tooth_number INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'healthy',
    notes TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(dental_patient_id, tooth_number),
    FOREIGN KEY (dental_patient_id) REFERENCES dental_patients(id)
);

-- Dental treatment history
CREATE TABLE IF NOT EXISTS dental_treatments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dental_patient_id INTEGER NOT NULL,
    tooth_number INTEGER NOT NULL,
    procedure_type TEXT NOT NULL,
    provider TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    treatment_date TEXT NOT NULL DEFAULT (datetime('now')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (dental_patient_id) REFERENCES dental_patients(id)
);

-- Dental preventive care
CREATE TABLE IF NOT EXISTS dental_preventive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dental_patient_id INTEGER NOT NULL,
    last_cleaning TEXT,
    next_cleaning TEXT,
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (dental_patient_id) REFERENCES dental_patients(id)
);

-- Mental health check-ins (privacy-first: all voluntary)
CREATE TABLE IF NOT EXISTS mental_checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    checkin_date TEXT NOT NULL DEFAULT (datetime('now')),
    mood INTEGER NOT NULL CHECK(mood BETWEEN 1 AND 5),
    sleep_quality INTEGER NOT NULL CHECK(sleep_quality BETWEEN 1 AND 5),
    appetite INTEGER NOT NULL CHECK(appetite BETWEEN 1 AND 5),
    energy INTEGER NOT NULL CHECK(energy BETWEEN 1 AND 5),
    anxiety_level INTEGER NOT NULL CHECK(anxiety_level BETWEEN 1 AND 5),
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Mental health provider notes (requires explicit consent)
CREATE TABLE IF NOT EXISTS mental_provider_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    note TEXT NOT NULL,
    patient_consent INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Veterinary visits
CREATE TABLE IF NOT EXISTS vet_visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id TEXT NOT NULL,
    visit_date TEXT NOT NULL DEFAULT (datetime('now')),
    condition TEXT NOT NULL,
    treatment TEXT NOT NULL DEFAULT '',
    provider TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""
