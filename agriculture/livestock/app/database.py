"""SQLite database setup and access for the livestock module."""

import sqlite3
from pathlib import Path
from typing import Any


_db_path: str = ":memory:"


def set_db_path(path: str) -> None:
    """Set the database file path."""
    global _db_path
    _db_path = path
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory enabled."""
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Initialize database schema."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS animals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            tag TEXT UNIQUE,
            species TEXT NOT NULL,
            breed TEXT NOT NULL DEFAULT '',
            sex TEXT NOT NULL CHECK(sex IN ('male', 'female', 'unknown')),
            birth_date TEXT,
            acquisition_date TEXT,
            sire_id INTEGER REFERENCES animals(id),
            dam_id INTEGER REFERENCES animals(id),
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'sold', 'deceased')),
            photo_path TEXT,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS breeding_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sire_id INTEGER NOT NULL REFERENCES animals(id),
            dam_id INTEGER NOT NULL REFERENCES animals(id),
            date_bred TEXT NOT NULL,
            expected_due_date TEXT,
            actual_due_date TEXT,
            outcome TEXT NOT NULL DEFAULT 'pending' CHECK(outcome IN ('pending', 'success', 'failure', 'abortion')),
            offspring_count INTEGER DEFAULT 0,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS feed_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            unit TEXT NOT NULL DEFAULT 'kg',
            calories_per_unit REAL NOT NULL DEFAULT 0,
            protein_pct REAL NOT NULL DEFAULT 0,
            notes TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS feed_requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            species TEXT NOT NULL,
            production_stage TEXT NOT NULL CHECK(production_stage IN ('maintenance', 'growing', 'pregnant', 'lactating')),
            min_weight_kg REAL NOT NULL DEFAULT 0,
            max_weight_kg REAL NOT NULL DEFAULT 9999,
            daily_dm_pct_bw REAL NOT NULL,
            crude_protein_pct REAL NOT NULL DEFAULT 0,
            notes TEXT NOT NULL DEFAULT '',
            UNIQUE(species, production_stage, min_weight_kg)
        );

        CREATE TABLE IF NOT EXISTS feed_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_type_id INTEGER NOT NULL REFERENCES feed_types(id),
            quantity REAL NOT NULL DEFAULT 0,
            low_threshold REAL NOT NULL DEFAULT 10,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS feed_consumption (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id INTEGER NOT NULL REFERENCES animals(id),
            feed_type_id INTEGER NOT NULL REFERENCES feed_types(id),
            quantity REAL NOT NULL,
            date TEXT NOT NULL DEFAULT (date('now')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS treatments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id INTEGER NOT NULL REFERENCES animals(id),
            date TEXT NOT NULL DEFAULT (date('now')),
            condition TEXT NOT NULL,
            treatment TEXT NOT NULL,
            medication TEXT NOT NULL DEFAULT '',
            dosage TEXT NOT NULL DEFAULT '',
            administered_by TEXT NOT NULL DEFAULT '',
            withdrawal_days INTEGER NOT NULL DEFAULT 0,
            withdrawal_end_date TEXT,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL DEFAULT '',
            quantity REAL NOT NULL DEFAULT 0,
            unit TEXT NOT NULL DEFAULT 'doses',
            low_threshold REAL NOT NULL DEFAULT 5,
            default_withdrawal_days INTEGER NOT NULL DEFAULT 0,
            notes TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS vaccinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id INTEGER NOT NULL REFERENCES animals(id),
            vaccine TEXT NOT NULL,
            date_given TEXT NOT NULL,
            next_due_date TEXT,
            administered_by TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS production_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id INTEGER NOT NULL REFERENCES animals(id),
            type TEXT NOT NULL CHECK(type IN ('milk', 'eggs', 'weight', 'wool', 'other')),
            value REAL NOT NULL,
            unit TEXT NOT NULL,
            date TEXT NOT NULL DEFAULT (date('now')),
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_animals_species ON animals(species);
        CREATE INDEX IF NOT EXISTS idx_animals_status ON animals(status);
        CREATE INDEX IF NOT EXISTS idx_breeding_sire ON breeding_events(sire_id);
        CREATE INDEX IF NOT EXISTS idx_breeding_dam ON breeding_events(dam_id);
        CREATE INDEX IF NOT EXISTS idx_treatments_animal ON treatments(animal_id);
        CREATE INDEX IF NOT EXISTS idx_production_animal ON production_records(animal_id);
        CREATE INDEX IF NOT EXISTS idx_production_date ON production_records(date);
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
