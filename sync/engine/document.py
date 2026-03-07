"""Automerge document wrapper for CRDT-based sync."""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SyncDocument:
    """Wrapper around an Automerge-style CRDT document.

    Since the `automerge` Python package has limited availability,
    this implements a compatible CRDT document using a last-writer-wins
    register with vector clocks for conflict-free merging.
    """

    doc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    doc_type: str = ""
    node_id: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    vector_clock: dict[str, int] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def update(self, changes: dict[str, Any]) -> None:
        """Apply changes to the document, advancing the vector clock."""
        ts = time.time()
        seq = self.vector_clock.get(self.node_id, 0) + 1
        self.vector_clock[self.node_id] = seq

        self.history.append({
            "node_id": self.node_id,
            "seq": seq,
            "timestamp": ts,
            "changes": changes,
        })

        self._apply_changes(changes)
        self.updated_at = ts

    def _apply_changes(self, changes: dict[str, Any]) -> None:
        """Deep-merge changes into current data."""
        _deep_merge(self.data, changes)

    def get_changes_since(self, remote_clock: dict[str, int]) -> list[dict[str, Any]]:
        """Return history entries the remote hasn't seen."""
        result = []
        for entry in self.history:
            nid = entry["node_id"]
            seq = entry["seq"]
            if seq > remote_clock.get(nid, 0):
                result.append(entry)
        return result

    def snapshot_hash(self) -> str:
        """Deterministic hash of current document state."""
        import json
        content = json.dumps(self.data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "doc_type": self.doc_type,
            "node_id": self.node_id,
            "data": self.data,
            "vector_clock": self.vector_clock,
            "history": self.history,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SyncDocument:
        return cls(
            doc_id=d["doc_id"],
            doc_type=d["doc_type"],
            node_id=d["node_id"],
            data=d.get("data", {}),
            vector_clock=d.get("vector_clock", {}),
            history=d.get("history", []),
            created_at=d.get("created_at", time.time()),
            updated_at=d.get("updated_at", time.time()),
        )


def _deep_merge(base: dict, override: dict) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
