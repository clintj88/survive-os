"""Backup status dashboard API.

Tracks backup history, sizes, and USB drive health.
"""

import os
import shutil
import sqlite3
from pathlib import Path

from shared.db import connect, execute, query
from shared.db.timestamps import utcnow

_STATUS_SCHEMA = """
CREATE TABLE IF NOT EXISTS backup_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module TEXT NOT NULL,
    backup_type TEXT NOT NULL DEFAULT 'snapshot',
    status TEXT NOT NULL DEFAULT 'completed',
    size_bytes INTEGER NOT NULL DEFAULT 0,
    duration_seconds REAL NOT NULL DEFAULT 0,
    backup_path TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_backup_history_module ON backup_history(module);
CREATE INDEX IF NOT EXISTS idx_backup_history_time ON backup_history(created_at);
"""


def init_status_db(conn: sqlite3.Connection) -> None:
    """Create backup status tables."""
    conn.executescript(_STATUS_SCHEMA)


def record_backup(
    conn: sqlite3.Connection,
    module: str,
    backup_type: str,
    status: str,
    size_bytes: int,
    duration_seconds: float,
    backup_path: str = "",
) -> int:
    """Record a backup event in the history."""
    return execute(
        conn,
        "INSERT INTO backup_history (module, backup_type, status, size_bytes, duration_seconds, backup_path, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (module, backup_type, status, size_bytes, duration_seconds, backup_path, utcnow()),
    )


def get_last_backup(conn: sqlite3.Connection, module: str) -> dict | None:
    """Get the most recent successful backup for a module."""
    rows = query(
        conn,
        "SELECT * FROM backup_history WHERE module = ? AND status = 'completed' ORDER BY created_at DESC LIMIT 1",
        (module,),
    )
    return rows[0] if rows else None


def get_all_last_backups(conn: sqlite3.Connection) -> list[dict]:
    """Get the most recent backup for each module."""
    return query(
        conn,
        """
        SELECT bh.* FROM backup_history bh
        INNER JOIN (
            SELECT module, MAX(created_at) as max_time
            FROM backup_history WHERE status = 'completed'
            GROUP BY module
        ) latest ON bh.module = latest.module AND bh.created_at = latest.max_time
        ORDER BY bh.module
        """,
    )


def get_backup_history(
    conn: sqlite3.Connection,
    module: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Get backup history, optionally filtered by module."""
    if module:
        return query(
            conn,
            "SELECT * FROM backup_history WHERE module = ? ORDER BY created_at DESC LIMIT ?",
            (module, limit),
        )
    return query(
        conn,
        "SELECT * FROM backup_history ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )


def get_drive_status(mount_point: str) -> dict:
    """Get USB drive health and free space information."""
    if not os.path.ismount(mount_point) and not os.path.isdir(mount_point):
        return {"mounted": False, "path": mount_point}

    usage = shutil.disk_usage(mount_point)
    return {
        "mounted": True,
        "path": mount_point,
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "percent_used": round(usage.used / usage.total * 100, 1) if usage.total > 0 else 0,
    }
