"""SQLite/SQLCipher database setup and access for Concepts.

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
        CREATE TABLE IF NOT EXISTS concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            short_name TEXT DEFAULT '',
            datatype TEXT NOT NULL CHECK (datatype IN ('numeric', 'coded', 'text', 'boolean', 'date', 'datetime')),
            concept_class TEXT NOT NULL CHECK (concept_class IN ('diagnosis', 'symptom', 'test', 'drug', 'procedure', 'finding', 'misc')),
            description TEXT DEFAULT '',
            units TEXT DEFAULT '',
            retired INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS concept_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id INTEGER NOT NULL,
            answer_concept_id INTEGER NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (concept_id) REFERENCES concepts(id),
            FOREIGN KEY (answer_concept_id) REFERENCES concepts(id)
        );

        CREATE TABLE IF NOT EXISTS concept_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id INTEGER NOT NULL,
            source TEXT NOT NULL CHECK (source IN ('icd10', 'snomed', 'loinc', 'local')),
            code TEXT NOT NULL,
            name TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (concept_id) REFERENCES concepts(id)
        );

        CREATE TABLE IF NOT EXISTS concept_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS concept_set_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            set_id INTEGER NOT NULL,
            concept_id INTEGER NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (set_id) REFERENCES concept_sets(id),
            FOREIGN KEY (concept_id) REFERENCES concepts(id)
        );

        CREATE INDEX IF NOT EXISTS idx_concepts_name ON concepts(name);
        CREATE INDEX IF NOT EXISTS idx_concepts_class ON concepts(concept_class);
        CREATE INDEX IF NOT EXISTS idx_concept_answers_concept ON concept_answers(concept_id);
        CREATE INDEX IF NOT EXISTS idx_concept_mappings_concept ON concept_mappings(concept_id);
        CREATE INDEX IF NOT EXISTS idx_concept_set_members_set ON concept_set_members(set_id);
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
