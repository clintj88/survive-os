"""SQLite database setup and access for the governance module."""

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
        -- Census
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dob TEXT,
            sex TEXT CHECK(sex IN ('M','F','X')),
            occupation TEXT DEFAULT '',
            housing_assignment TEXT DEFAULT '',
            arrival_date TEXT NOT NULL DEFAULT (date('now')),
            status TEXT NOT NULL DEFAULT 'active'
                CHECK(status IN ('active','deceased','departed')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS person_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            rating INTEGER NOT NULL DEFAULT 1 CHECK(rating BETWEEN 1 AND 5),
            FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
            UNIQUE(person_id, category)
        );

        -- Voting
        CREATE TABLE IF NOT EXISTS ballots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            ballot_type TEXT NOT NULL DEFAULT 'yes_no'
                CHECK(ballot_type IN ('yes_no','multiple_choice','ranked_choice')),
            options TEXT NOT NULL DEFAULT '["yes","no"]',
            voting_period_start TEXT NOT NULL DEFAULT (datetime('now')),
            voting_period_end TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ballot_id INTEGER NOT NULL,
            voter_id INTEGER NOT NULL,
            choice TEXT NOT NULL,
            cast_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (ballot_id) REFERENCES ballots(id),
            UNIQUE(ballot_id, voter_id)
        );

        CREATE TABLE IF NOT EXISTS vote_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ballot_id INTEGER NOT NULL,
            voter_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            detail TEXT NOT NULL DEFAULT '',
            logged_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Resources
        CREATE TABLE IF NOT EXISTS resource_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL
                CHECK(category IN ('food','water','fuel','medicine','building_materials','tools')),
            name TEXT NOT NULL,
            quantity REAL NOT NULL DEFAULT 0,
            unit TEXT NOT NULL DEFAULT 'units',
            low_threshold REAL NOT NULL DEFAULT 10,
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(category, name)
        );

        CREATE TABLE IF NOT EXISTS distribution_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id INTEGER NOT NULL,
            person_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            distributed_at TEXT NOT NULL DEFAULT (datetime('now')),
            distributed_by TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (resource_id) REFERENCES resource_inventory(id),
            FOREIGN KEY (person_id) REFERENCES persons(id)
        );

        -- Treaties
        CREATE TABLE IF NOT EXISTS treaties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            parties TEXT NOT NULL DEFAULT '',
            content TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'draft'
                CHECK(status IN ('draft','active','expired','revoked')),
            effective_date TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS treaty_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            treaty_id INTEGER NOT NULL,
            version_num INTEGER NOT NULL DEFAULT 1,
            content TEXT NOT NULL,
            changed_by TEXT NOT NULL DEFAULT '',
            changed_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (treaty_id) REFERENCES treaties(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS treaty_signatories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            treaty_id INTEGER NOT NULL,
            person_name TEXT NOT NULL,
            signed_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (treaty_id) REFERENCES treaties(id) ON DELETE CASCADE,
            UNIQUE(treaty_id, person_name)
        );

        -- Disputes
        CREATE TABLE IF NOT EXISTS disputes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parties TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'governance'
                CHECK(category IN ('property','personal','trade','governance')),
            status TEXT NOT NULL DEFAULT 'open'
                CHECK(status IN ('open','mediation','resolved','appealed')),
            filed_date TEXT NOT NULL DEFAULT (date('now')),
            resolution_notes TEXT DEFAULT '',
            outcome TEXT DEFAULT '',
            precedent_id INTEGER,
            FOREIGN KEY (precedent_id) REFERENCES disputes(id)
        );

        -- Duties
        CREATE TABLE IF NOT EXISTS duty_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            duty_type TEXT NOT NULL
                CHECK(duty_type IN ('watch','cooking','cleaning','farming','maintenance','teaching')),
            duty_date TEXT NOT NULL,
            shift TEXT NOT NULL DEFAULT 'morning'
                CHECK(shift IN ('morning','afternoon','night')),
            status TEXT NOT NULL DEFAULT 'assigned'
                CHECK(status IN ('assigned','completed','swapped')),
            FOREIGN KEY (person_id) REFERENCES persons(id),
            UNIQUE(person_id, duty_date, shift)
        );

        CREATE TABLE IF NOT EXISTS duty_swap_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id INTEGER NOT NULL,
            requester_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending','approved','denied')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (assignment_id) REFERENCES duty_assignments(id),
            FOREIGN KEY (requester_id) REFERENCES persons(id),
            FOREIGN KEY (target_id) REFERENCES persons(id)
        );

        -- Journal
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL DEFAULT (date('now')),
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'daily_log'
                CHECK(category IN ('daily_log','event','milestone','memorial')),
            attachments TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Civil Registry
        CREATE TABLE IF NOT EXISTS birth_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_name TEXT NOT NULL,
            dob TEXT NOT NULL,
            parent1 TEXT NOT NULL DEFAULT '',
            parent2 TEXT NOT NULL DEFAULT '',
            location TEXT NOT NULL DEFAULT '',
            attendant TEXT NOT NULL DEFAULT '',
            recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS death_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_name TEXT NOT NULL,
            date_of_death TEXT NOT NULL,
            cause TEXT NOT NULL DEFAULT '',
            location TEXT NOT NULL DEFAULT '',
            witnessed_by TEXT NOT NULL DEFAULT '',
            recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS marriage_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            party1 TEXT NOT NULL,
            party2 TEXT NOT NULL,
            marriage_date TEXT NOT NULL,
            officiant TEXT NOT NULL DEFAULT '',
            witnesses TEXT NOT NULL DEFAULT '',
            recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Calendar
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_time TEXT DEFAULT '',
            location TEXT DEFAULT '',
            event_type TEXT NOT NULL DEFAULT 'meeting'
                CHECK(event_type IN ('meeting','celebration','memorial','seasonal','work')),
            description TEXT NOT NULL DEFAULT '',
            recurring INTEGER NOT NULL DEFAULT 0,
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
