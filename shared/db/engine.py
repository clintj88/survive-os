"""SQLite/SQLCipher connection factory with WAL mode, foreign keys, and PRAGMA tuning."""

import sqlite3
from pathlib import Path
from typing import Any

# Try to use SQLCipher; fall back to plain sqlite3
try:
    from pysqlcipher3 import dbapi2 as sqlcipher  # type: ignore[import-untyped]
    HAS_SQLCIPHER = True
except ImportError:
    HAS_SQLCIPHER = False


def connect(
    db_path: str,
    key: str = "",
    wal_mode: bool = True,
    foreign_keys: bool = True,
) -> sqlite3.Connection:
    """Create a database connection with production-grade PRAGMA settings.

    Args:
        db_path: Path to the SQLite database file, or ":memory:".
        key: Encryption key for SQLCipher. Empty string means no encryption.
        wal_mode: Enable WAL journal mode for concurrent reads.
        foreign_keys: Enable foreign key constraint enforcement.

    Returns:
        A configured sqlite3.Connection with Row factory.
    """
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    if HAS_SQLCIPHER and key:
        conn = sqlcipher.connect(db_path)
        conn.execute("PRAGMA key=?", (key,))
    else:
        conn = sqlite3.connect(db_path)

    conn.row_factory = sqlite3.Row

    if wal_mode:
        conn.execute("PRAGMA journal_mode=WAL")
    if foreign_keys:
        conn.execute("PRAGMA foreign_keys=ON")

    # Performance tuning safe for Raspberry Pi 4
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-8000")  # 8MB cache
    conn.execute("PRAGMA busy_timeout=5000")

    return conn


def query(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    """Execute a query and return results as list of dicts."""
    rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def execute(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> int:
    """Execute a statement, commit, and return lastrowid."""
    cursor = conn.execute(sql, params)
    conn.commit()
    return cursor.lastrowid or 0


def executemany(conn: sqlite3.Connection, sql: str, param_seq: list[tuple[Any, ...]]) -> None:
    """Execute a statement with multiple parameter sets and commit."""
    conn.executemany(sql, param_seq)
    conn.commit()


def executescript(conn: sqlite3.Connection, sql: str) -> None:
    """Execute a multi-statement SQL script and commit."""
    conn.executescript(sql)
    conn.commit()
