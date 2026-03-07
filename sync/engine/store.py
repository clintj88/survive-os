"""Document store backed by filesystem with SQLite index."""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

from .document import SyncDocument

logger = logging.getLogger(__name__)


class DocumentStore:
    """Stores Automerge documents as JSON files with SQLite index for lookup."""

    def __init__(self, db_path: str, storage_path: str) -> None:
        self.db_path = Path(db_path)
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def init(self) -> None:
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                doc_type TEXT NOT NULL,
                node_id TEXT NOT NULL,
                snapshot_hash TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_doc_type ON documents(doc_type)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_updated ON documents(updated_at)"
        )
        self._conn.commit()

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("DocumentStore not initialized — call init() first")
        return self._conn

    def save(self, doc: SyncDocument) -> None:
        doc_path = self._doc_path(doc.doc_id)
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(json.dumps(doc.to_dict(), default=str))

        self.conn.execute(
            """INSERT OR REPLACE INTO documents
               (doc_id, doc_type, node_id, snapshot_hash, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (doc.doc_id, doc.doc_type, doc.node_id,
             doc.snapshot_hash(), doc.created_at, doc.updated_at),
        )
        self.conn.commit()

    def load(self, doc_id: str) -> SyncDocument | None:
        doc_path = self._doc_path(doc_id)
        if not doc_path.exists():
            return None
        data = json.loads(doc_path.read_text())
        return SyncDocument.from_dict(data)

    def delete(self, doc_id: str) -> bool:
        doc_path = self._doc_path(doc_id)
        if doc_path.exists():
            doc_path.unlink()
        self.conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        self.conn.commit()
        return True

    def list_by_type(self, doc_type: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM documents WHERE doc_type = ? ORDER BY updated_at DESC",
            (doc_type,),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_modified_since(self, since: float) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM documents WHERE updated_at > ? ORDER BY updated_at ASC",
            (since,),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_all(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM documents ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()
        return row["cnt"]

    def _doc_path(self, doc_id: str) -> Path:
        # Shard by first 2 chars of doc_id to avoid huge flat directories
        return self.storage_path / doc_id[:2] / f"{doc_id}.json"

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
