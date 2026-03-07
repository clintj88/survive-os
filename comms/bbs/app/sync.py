"""Automerge CRDT sync stub for BBS module.

This module provides the interface for CRDT-based sync of BBS data
across offline-first nodes. The actual Automerge integration will be
connected when the sync engine module is available.
"""

from typing import Any


class SyncState:
    """Tracks sync state for CRDT merging."""

    def __init__(self) -> None:
        self._vector_clock: dict[str, int] = {}

    def get_clock(self) -> dict[str, int]:
        return self._vector_clock.copy()

    def update_clock(self, node_id: str, seq: int) -> None:
        self._vector_clock[node_id] = max(
            self._vector_clock.get(node_id, 0), seq
        )


_sync_state = SyncState()


def get_sync_status() -> dict[str, Any]:
    return {
        "enabled": False,
        "engine": "automerge",
        "clock": _sync_state.get_clock(),
        "status": "awaiting_sync_engine",
    }


def record_change(node_id: str, seq: int) -> None:
    _sync_state.update_clock(node_id, seq)
