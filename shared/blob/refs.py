"""Reference tracking for content-addressed blobs.

SQLite table mapping (record_type, record_id) -> blob_hash with
reference counting for garbage collection.
"""

import sqlite3

from shared.db import connect, execute, query

_REFS_SCHEMA = """
CREATE TABLE IF NOT EXISTS _blob_refs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type TEXT NOT NULL,
    record_id TEXT NOT NULL,
    blob_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(record_type, record_id, blob_hash)
);
CREATE INDEX IF NOT EXISTS idx_blob_refs_hash ON _blob_refs(blob_hash);
CREATE INDEX IF NOT EXISTS idx_blob_refs_record ON _blob_refs(record_type, record_id);
"""


def init_refs_table(conn: sqlite3.Connection) -> None:
    """Create the _blob_refs table if it doesn't exist."""
    conn.executescript(_REFS_SCHEMA)


def add_ref(
    conn: sqlite3.Connection,
    record_type: str,
    record_id: str,
    blob_hash: str,
) -> None:
    """Add a reference from a record to a blob."""
    conn.execute(
        "INSERT OR IGNORE INTO _blob_refs (record_type, record_id, blob_hash) VALUES (?, ?, ?)",
        (record_type, record_id, blob_hash),
    )
    conn.commit()


def remove_ref(
    conn: sqlite3.Connection,
    record_type: str,
    record_id: str,
    blob_hash: str,
) -> None:
    """Remove a specific reference from a record to a blob."""
    conn.execute(
        "DELETE FROM _blob_refs WHERE record_type = ? AND record_id = ? AND blob_hash = ?",
        (record_type, record_id, blob_hash),
    )
    conn.commit()


def remove_all_refs(
    conn: sqlite3.Connection,
    record_type: str,
    record_id: str,
) -> None:
    """Remove all blob references for a record."""
    conn.execute(
        "DELETE FROM _blob_refs WHERE record_type = ? AND record_id = ?",
        (record_type, record_id),
    )
    conn.commit()


def ref_count(conn: sqlite3.Connection, blob_hash: str) -> int:
    """Get the number of references to a blob."""
    rows = query(
        conn,
        "SELECT COUNT(*) as cnt FROM _blob_refs WHERE blob_hash = ?",
        (blob_hash,),
    )
    return rows[0]["cnt"] if rows else 0


def get_refs_for_record(
    conn: sqlite3.Connection, record_type: str, record_id: str
) -> list[str]:
    """Get all blob hashes referenced by a record."""
    rows = query(
        conn,
        "SELECT blob_hash FROM _blob_refs WHERE record_type = ? AND record_id = ?",
        (record_type, record_id),
    )
    return [r["blob_hash"] for r in rows]


def get_unreferenced_hashes(conn: sqlite3.Connection, known_hashes: list[str]) -> list[str]:
    """Given a list of blob hashes on disk, return those with zero references."""
    if not known_hashes:
        return []
    placeholders = ",".join("?" * len(known_hashes))
    rows = query(
        conn,
        f"SELECT blob_hash, COUNT(*) as cnt FROM _blob_refs WHERE blob_hash IN ({placeholders}) GROUP BY blob_hash",
        tuple(known_hashes),
    )
    referenced = {r["blob_hash"] for r in rows}
    return [h for h in known_hashes if h not in referenced]


def gc_blobs(conn: sqlite3.Connection, base_dir: str) -> list[str]:
    """Garbage collect unreferenced blobs. Returns list of removed hashes."""
    from . import store

    all_hashes = store.list_blobs(base_dir)
    unreferenced = get_unreferenced_hashes(conn, all_hashes)
    removed = []
    for h in unreferenced:
        if store.delete_blob(base_dir, h):
            removed.append(h)
    return removed
