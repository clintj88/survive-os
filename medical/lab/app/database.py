"""SQLite/SQLCipher database setup and access for Lab.

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
        CREATE TABLE IF NOT EXISTS test_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            concept_id TEXT,
            specimen_type TEXT NOT NULL DEFAULT 'blood'
                CHECK (specimen_type IN ('blood', 'urine', 'stool', 'swab', 'csf', 'other')),
            ref_range_min REAL,
            ref_range_max REAL,
            critical_low REAL,
            critical_high REAL,
            units TEXT DEFAULT '',
            description TEXT DEFAULT '',
            turnaround_hours INTEGER DEFAULT 24,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS lab_panels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS panel_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            panel_id INTEGER NOT NULL,
            test_id INTEGER NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (panel_id) REFERENCES lab_panels(id),
            FOREIGN KEY (test_id) REFERENCES test_catalog(id)
        );

        CREATE TABLE IF NOT EXISTS lab_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            test_id INTEGER,
            panel_id INTEGER,
            ordered_by TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'routine'
                CHECK (priority IN ('routine', 'urgent', 'stat')),
            clinical_indication TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'ordered'
                CHECK (status IN ('ordered', 'collected', 'processing', 'completed', 'cancelled')),
            ordered_at TEXT NOT NULL DEFAULT (datetime('now')),
            collected_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (test_id) REFERENCES test_catalog(id),
            FOREIGN KEY (panel_id) REFERENCES lab_panels(id)
        );

        CREATE TABLE IF NOT EXISTS lab_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            test_id INTEGER NOT NULL,
            value TEXT DEFAULT '',
            numeric_value REAL,
            units TEXT DEFAULT '',
            interpretation TEXT DEFAULT '',
            performed_by TEXT DEFAULT '',
            result_date TEXT NOT NULL DEFAULT (datetime('now')),
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (order_id) REFERENCES lab_orders(id),
            FOREIGN KEY (test_id) REFERENCES test_catalog(id)
        );

        CREATE INDEX IF NOT EXISTS idx_panel_tests_panel ON panel_tests(panel_id);
        CREATE INDEX IF NOT EXISTS idx_lab_orders_patient ON lab_orders(patient_id);
        CREATE INDEX IF NOT EXISTS idx_lab_orders_status ON lab_orders(status);
        CREATE INDEX IF NOT EXISTS idx_lab_results_order ON lab_results(order_id);
        CREATE INDEX IF NOT EXISTS idx_lab_results_test ON lab_results(test_id);
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
