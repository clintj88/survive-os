"""SQLite database setup and access for the energy/fuel tracking module."""

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
        -- Solar panels
        CREATE TABLE IF NOT EXISTS solar_panels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rated_watts REAL NOT NULL,
            location TEXT NOT NULL DEFAULT '',
            install_date TEXT,
            orientation TEXT NOT NULL DEFAULT 'south',
            tilt_angle REAL NOT NULL DEFAULT 30.0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS solar_output (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            panel_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            watts_output REAL NOT NULL,
            irradiance REAL,
            FOREIGN KEY (panel_id) REFERENCES solar_panels(id)
        );

        -- Battery banks
        CREATE TABLE IF NOT EXISTS battery_banks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('lead-acid','lithium','nickel')),
            capacity_ah REAL NOT NULL,
            voltage REAL NOT NULL,
            num_cells INTEGER NOT NULL DEFAULT 1,
            install_date TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS battery_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            voltage REAL NOT NULL,
            current_amps REAL NOT NULL DEFAULT 0.0,
            soc_percent REAL NOT NULL,
            temperature REAL,
            FOREIGN KEY (bank_id) REFERENCES battery_banks(id)
        );

        -- Fuel reserves
        CREATE TABLE IF NOT EXISTS fuel_storage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fuel_type TEXT NOT NULL CHECK(fuel_type IN (
                'gasoline','diesel','propane','firewood','kerosene','ethanol'
            )),
            quantity REAL NOT NULL,
            unit TEXT NOT NULL CHECK(unit IN ('liters','gallons','kg','cords')),
            storage_location TEXT NOT NULL DEFAULT '',
            date_added TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS fuel_consumption (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fuel_type TEXT NOT NULL,
            quantity_used REAL NOT NULL,
            unit TEXT NOT NULL CHECK(unit IN ('liters','gallons','kg','cords')),
            purpose TEXT NOT NULL DEFAULT '',
            date TEXT NOT NULL DEFAULT (date('now')),
            used_by TEXT NOT NULL DEFAULT ''
        );

        -- Generators
        CREATE TABLE IF NOT EXISTS generators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            fuel_type TEXT NOT NULL,
            rated_kw REAL NOT NULL,
            location TEXT NOT NULL DEFAULT '',
            install_date TEXT,
            total_runtime_hours REAL NOT NULL DEFAULT 0.0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS generator_runtime (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            generator_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            fuel_consumed REAL NOT NULL DEFAULT 0.0,
            load_percent REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY (generator_id) REFERENCES generators(id)
        );

        CREATE TABLE IF NOT EXISTS generator_maintenance_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            generator_id INTEGER NOT NULL,
            task TEXT NOT NULL,
            interval_hours REAL NOT NULL,
            last_performed_hours REAL NOT NULL DEFAULT 0.0,
            last_performed_date TEXT,
            FOREIGN KEY (generator_id) REFERENCES generators(id)
        );

        CREATE TABLE IF NOT EXISTS generator_maintenance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            generator_id INTEGER NOT NULL,
            task TEXT NOT NULL,
            performed_by TEXT NOT NULL DEFAULT '',
            performed_date TEXT NOT NULL DEFAULT (datetime('now')),
            at_runtime_hours REAL NOT NULL DEFAULT 0.0,
            notes TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (generator_id) REFERENCES generators(id)
        );

        -- Power budget loads
        CREATE TABLE IF NOT EXISTS power_loads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            watts_draw REAL NOT NULL,
            priority TEXT NOT NULL DEFAULT 'optional' CHECK(priority IN (
                'critical','important','optional'
            )),
            hours_per_day REAL NOT NULL DEFAULT 0.0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
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
