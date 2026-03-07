"""Point-in-time database snapshots using SQLite online backup API.

Consistent backups without stopping services.
"""

import os
import sqlite3
import tempfile
from pathlib import Path

from shared.db import connect
from shared.db.timestamps import utcnow


def snapshot_database(
    source_path: str,
    dest_path: str,
    source_key: str = "",
    pages: int = -1,
) -> dict:
    """Create a point-in-time snapshot of a SQLite database.

    Uses the SQLite online backup API for a consistent copy
    without stopping the service that owns the database.

    Args:
        source_path: Path to the live database.
        dest_path: Path for the snapshot file.
        source_key: SQLCipher key if the source is encrypted.
        pages: Pages per backup step (-1 = all at once).

    Returns:
        Dict with snapshot metadata.
    """
    Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
    source_conn = connect(source_path, key=source_key, wal_mode=True)
    dest_conn = sqlite3.connect(dest_path)

    try:
        source_conn.backup(dest_conn, pages=pages)
    finally:
        source_conn.close()
        dest_conn.close()

    size = os.path.getsize(dest_path)
    return {
        "source": source_path,
        "snapshot": dest_path,
        "size": size,
        "created_at": utcnow(),
    }


def snapshot_all_modules(
    modules: dict[str, dict],
    backup_dir: str,
) -> list[dict]:
    """Snapshot all module databases.

    Args:
        modules: Dict of module_name -> {"db_path": str, "key": str (optional)}.
        backup_dir: Base directory for snapshots.

    Returns:
        List of snapshot metadata dicts.
    """
    results = []
    timestamp = utcnow().replace(":", "-").replace(".", "-")
    for name, config in modules.items():
        db_path = config.get("db_path", "")
        if not db_path or not Path(db_path).exists():
            continue
        dest = os.path.join(backup_dir, name, f"{name}-{timestamp}.db")
        key = config.get("key", "")
        meta = snapshot_database(db_path, dest, source_key=key)
        meta["module"] = name
        results.append(meta)
    return results
