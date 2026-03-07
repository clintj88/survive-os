"""SQLite/SQLCipher database setup and access for Programs.

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
        CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS program_workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS workflow_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            initial INTEGER NOT NULL DEFAULT 0,
            terminal INTEGER NOT NULL DEFAULT 0,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (workflow_id) REFERENCES program_workflows(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS state_transitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_state_id INTEGER NOT NULL,
            to_state_id INTEGER NOT NULL,
            FOREIGN KEY (from_state_id) REFERENCES workflow_states(id) ON DELETE CASCADE,
            FOREIGN KEY (to_state_id) REFERENCES workflow_states(id) ON DELETE CASCADE,
            UNIQUE(from_state_id, to_state_id)
        );

        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            program_id INTEGER NOT NULL,
            enrolled_by TEXT NOT NULL,
            enrollment_date TEXT NOT NULL DEFAULT (datetime('now')),
            completion_date TEXT,
            outcome TEXT NOT NULL DEFAULT 'active'
                CHECK (outcome IN ('active', 'completed', 'defaulted', 'transferred_out', 'died')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (program_id) REFERENCES programs(id)
        );

        CREATE TABLE IF NOT EXISTS enrollment_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enrollment_id INTEGER NOT NULL,
            state_id INTEGER NOT NULL,
            start_date TEXT NOT NULL DEFAULT (datetime('now')),
            end_date TEXT,
            changed_by TEXT NOT NULL,
            reason TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE,
            FOREIGN KEY (state_id) REFERENCES workflow_states(id)
        );

        CREATE INDEX IF NOT EXISTS idx_workflows_program ON program_workflows(program_id);
        CREATE INDEX IF NOT EXISTS idx_states_workflow ON workflow_states(workflow_id);
        CREATE INDEX IF NOT EXISTS idx_transitions_from ON state_transitions(from_state_id);
        CREATE INDEX IF NOT EXISTS idx_transitions_to ON state_transitions(to_state_id);
        CREATE INDEX IF NOT EXISTS idx_enrollments_program ON enrollments(program_id);
        CREATE INDEX IF NOT EXISTS idx_enrollments_patient ON enrollments(patient_id);
        CREATE INDEX IF NOT EXISTS idx_enrollment_states_enrollment ON enrollment_states(enrollment_id);
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
