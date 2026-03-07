"""SQLite/SQLCipher database setup for the pharmacy module.

Production uses pysqlcipher3 for encryption at rest.
Falls back to standard sqlite3 for testing environments.
"""

import sqlite3
from pathlib import Path
from typing import Any


_db_path: str = ":memory:"
_db_key: str = ""

try:
    from pysqlcipher3 import dbapi2 as sqlcipher  # type: ignore[import-untyped]
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
    else:
        conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Initialize the pharmacy database schema."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            generic_name TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT '',
            form TEXT NOT NULL DEFAULT 'tablet',
            strength TEXT NOT NULL DEFAULT '',
            unit TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS inventory_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medication_id INTEGER NOT NULL,
            lot_number TEXT NOT NULL DEFAULT '',
            quantity INTEGER NOT NULL DEFAULT 0,
            expiration_date TEXT NOT NULL,
            supplier TEXT NOT NULL DEFAULT '',
            date_received TEXT NOT NULL DEFAULT (datetime('now')),
            storage_location TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (medication_id) REFERENCES medications(id)
        );

        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            medication_id INTEGER NOT NULL,
            dosage TEXT NOT NULL,
            frequency TEXT NOT NULL,
            duration TEXT NOT NULL DEFAULT '',
            prescriber TEXT NOT NULL,
            date_prescribed TEXT NOT NULL DEFAULT (datetime('now')),
            status TEXT NOT NULL DEFAULT 'active',
            refills_remaining INTEGER NOT NULL DEFAULT 0,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (medication_id) REFERENCES medications(id)
        );

        CREATE TABLE IF NOT EXISTS dispensing_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_id INTEGER NOT NULL,
            lot_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            date_dispensed TEXT NOT NULL DEFAULT (datetime('now')),
            dispensed_by TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (prescription_id) REFERENCES prescriptions(id),
            FOREIGN KEY (lot_id) REFERENCES inventory_lots(id)
        );

        CREATE TABLE IF NOT EXISTS drug_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drug_a TEXT NOT NULL,
            drug_b TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'moderate',
            description TEXT NOT NULL DEFAULT '',
            mechanism TEXT NOT NULL DEFAULT '',
            recommendation TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS natural_medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            common_names TEXT NOT NULL DEFAULT '',
            uses TEXT NOT NULL DEFAULT '',
            preparation TEXT NOT NULL DEFAULT '',
            dosage TEXT NOT NULL DEFAULT '',
            contraindications TEXT NOT NULL DEFAULT '',
            drug_interactions TEXT NOT NULL DEFAULT '',
            habitat TEXT NOT NULL DEFAULT '',
            identification TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS dosing_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medication_name TEXT NOT NULL,
            indication TEXT NOT NULL DEFAULT '',
            age_min_months INTEGER NOT NULL DEFAULT 0,
            age_max_months INTEGER NOT NULL DEFAULT 2160,
            dose_mg_per_kg REAL NOT NULL DEFAULT 0,
            frequency_hours INTEGER NOT NULL DEFAULT 8,
            max_single_dose_mg REAL NOT NULL DEFAULT 0,
            max_daily_dose_mg REAL NOT NULL DEFAULT 0,
            adult_dose_mg REAL NOT NULL DEFAULT 0,
            notes TEXT NOT NULL DEFAULT ''
        );

        CREATE INDEX IF NOT EXISTS idx_lots_medication ON inventory_lots(medication_id);
        CREATE INDEX IF NOT EXISTS idx_lots_expiration ON inventory_lots(expiration_date);
        CREATE INDEX IF NOT EXISTS idx_prescriptions_patient ON prescriptions(patient_id);
        CREATE INDEX IF NOT EXISTS idx_prescriptions_status ON prescriptions(status);
        CREATE INDEX IF NOT EXISTS idx_dispensing_prescription ON dispensing_log(prescription_id);
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


def execute_many(sql: str, params_list: list[tuple[Any, ...]]) -> None:
    """Execute a statement with multiple parameter sets."""
    conn = get_connection()
    try:
        conn.executemany(sql, params_list)
        conn.commit()
    finally:
        conn.close()
