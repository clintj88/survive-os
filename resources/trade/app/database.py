"""SQLite database setup and access for the trade/barter ledger."""

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
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL DEFAULT (datetime('now')),
            party_a TEXT NOT NULL,
            party_b TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'completed', 'disputed', 'cancelled')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS trade_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id INTEGER NOT NULL,
            side TEXT NOT NULL CHECK (side IN ('give', 'receive')),
            item_description TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT NOT NULL,
            value_in_labor_hours REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS exchange_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commodity_a TEXT NOT NULL,
            commodity_b TEXT NOT NULL,
            rate REAL NOT NULL,
            set_by TEXT NOT NULL DEFAULT 'system',
            effective_date TEXT NOT NULL DEFAULT (datetime('now')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS market_days (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            location TEXT NOT NULL,
            organizer TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'upcoming'
                CHECK (status IN ('upcoming', 'active', 'completed')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS market_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market_id INTEGER NOT NULL,
            person TEXT NOT NULL,
            item_description TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT NOT NULL,
            asking_price_hours REAL NOT NULL DEFAULT 0,
            type TEXT NOT NULL DEFAULT 'offer'
                CHECK (type IN ('offer', 'want')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (market_id) REFERENCES market_days(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_name TEXT NOT NULL,
            skill_category TEXT NOT NULL
                CHECK (skill_category IN ('farming', 'medical', 'mechanical',
                    'construction', 'teaching', 'cooking', 'security',
                    'crafting', 'technology')),
            skill_name TEXT NOT NULL,
            proficiency TEXT NOT NULL DEFAULT 'beginner'
                CHECK (proficiency IN ('beginner', 'intermediate', 'expert')),
            hourly_rate REAL NOT NULL DEFAULT 1.0,
            available INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_trades_party_a ON trades(party_a);
        CREATE INDEX IF NOT EXISTS idx_trades_party_b ON trades(party_b);
        CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
        CREATE INDEX IF NOT EXISTS idx_trade_items_trade_id ON trade_items(trade_id);
        CREATE INDEX IF NOT EXISTS idx_exchange_rates_commodities
            ON exchange_rates(commodity_a, commodity_b);
        CREATE INDEX IF NOT EXISTS idx_market_days_status ON market_days(status);
        CREATE INDEX IF NOT EXISTS idx_market_listings_market
            ON market_listings(market_id);
        CREATE INDEX IF NOT EXISTS idx_skills_category ON skills(skill_category);
        CREATE INDEX IF NOT EXISTS idx_skills_person ON skills(person_name);
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
