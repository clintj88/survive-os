"""SQLite database setup and access for the seed bank."""

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
        CREATE TABLE IF NOT EXISTS seed_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            species TEXT NOT NULL,
            variety TEXT NOT NULL DEFAULT '',
            quantity REAL NOT NULL DEFAULT 0,
            unit TEXT NOT NULL DEFAULT 'grams',
            source TEXT NOT NULL DEFAULT '',
            date_collected TEXT NOT NULL DEFAULT (date('now')),
            storage_location TEXT NOT NULL DEFAULT '',
            storage_temp REAL,
            storage_humidity REAL,
            low_stock_threshold REAL NOT NULL DEFAULT 50,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('deposit', 'withdrawal')),
            amount REAL NOT NULL,
            reason TEXT NOT NULL DEFAULT '',
            performed_by TEXT NOT NULL DEFAULT 'system',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (lot_id) REFERENCES seed_lots(id)
        );

        CREATE TABLE IF NOT EXISTS germination_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id INTEGER NOT NULL,
            date_tested TEXT NOT NULL DEFAULT (date('now')),
            sample_size INTEGER NOT NULL,
            germination_count INTEGER NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (lot_id) REFERENCES seed_lots(id)
        );

        CREATE TABLE IF NOT EXISTS exchange_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id INTEGER,
            type TEXT NOT NULL CHECK(type IN ('offer', 'request')),
            species TEXT NOT NULL,
            variety TEXT NOT NULL DEFAULT '',
            quantity_available REAL NOT NULL DEFAULT 0,
            unit TEXT NOT NULL DEFAULT 'grams',
            description TEXT NOT NULL DEFAULT '',
            contact TEXT NOT NULL DEFAULT '',
            community TEXT NOT NULL DEFAULT 'local',
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'fulfilled', 'cancelled')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (lot_id) REFERENCES seed_lots(id)
        );

        CREATE INDEX IF NOT EXISTS idx_seed_lots_species ON seed_lots(species);
        CREATE INDEX IF NOT EXISTS idx_ledger_lot_id ON ledger(lot_id);
        CREATE INDEX IF NOT EXISTS idx_germination_lot_id ON germination_tests(lot_id);
        CREATE INDEX IF NOT EXISTS idx_exchange_status ON exchange_listings(status);
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
