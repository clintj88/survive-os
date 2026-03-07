"""SQLite database setup and access for the knowledge base."""

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
    """Initialize database schema and FTS5 table."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            slug TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            category_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            summary TEXT NOT NULL DEFAULT '',
            author TEXT NOT NULL DEFAULT 'system',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
            title, content, summary,
            content='articles',
            content_rowid='id'
        );

        CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
            INSERT INTO articles_fts(rowid, title, content, summary)
            VALUES (new.id, new.title, new.content, new.summary);
        END;

        CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
            INSERT INTO articles_fts(articles_fts, rowid, title, content, summary)
            VALUES ('delete', old.id, old.title, old.content, old.summary);
        END;

        CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
            INSERT INTO articles_fts(articles_fts, rowid, title, content, summary)
            VALUES ('delete', old.id, old.title, old.content, old.summary);
            INSERT INTO articles_fts(rowid, title, content, summary)
            VALUES (new.id, new.title, new.content, new.summary);
        END;
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
