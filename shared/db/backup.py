"""Backup utilities using the SQLite online backup API."""

import sqlite3
from pathlib import Path

from . import engine


def backup_to_file(
    source_conn: sqlite3.Connection,
    dest_path: str,
    dest_key: str = "",
    pages: int = -1,
) -> None:
    """Back up a database to a file using SQLite's online backup API.

    Args:
        source_conn: The live database connection to back up.
        dest_path: Path for the backup file.
        dest_key: Optional SQLCipher key for the backup (encrypted export).
        pages: Number of pages per step (-1 = all at once).
    """
    Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
    dest_conn = engine.connect(dest_path, key=dest_key, wal_mode=False)
    try:
        source_conn.backup(dest_conn, pages=pages)
    finally:
        dest_conn.close()


def restore_from_file(
    backup_path: str,
    dest_conn: sqlite3.Connection,
    backup_key: str = "",
    pages: int = -1,
) -> None:
    """Restore a database from a backup file.

    Args:
        backup_path: Path to the backup file.
        dest_conn: The target database connection to restore into.
        backup_key: Optional SQLCipher key if the backup is encrypted.
        pages: Number of pages per step (-1 = all at once).
    """
    source_conn = engine.connect(backup_path, key=backup_key, wal_mode=False)
    try:
        source_conn.backup(dest_conn, pages=pages)
    finally:
        source_conn.close()
