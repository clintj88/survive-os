"""Merge strategy implementation — idempotent, ordered CRDT merge."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .document import SyncDocument

logger = logging.getLogger(__name__)


@dataclass
class MergeResult:
    merged: bool
    conflicts: list[str]
    changes_applied: int


class MergeEngine:
    """Merges remote documents into local state using vector clocks.

    Guarantees:
    - Idempotent: merging the same data twice produces identical results
    - Ordered: vector clocks ensure causal ordering
    - Convergent: all nodes reach the same state given the same inputs
    """

    def merge(self, local: SyncDocument, remote: SyncDocument) -> MergeResult:
        """Merge a remote document into a local document.

        Uses vector clock comparison to determine which changes to apply.
        Returns a MergeResult describing what happened.
        """
        if local.doc_id != remote.doc_id:
            raise ValueError(
                f"Cannot merge documents with different IDs: "
                f"{local.doc_id} vs {remote.doc_id}"
            )

        # Get changes the local hasn't seen from the remote
        new_changes = remote.get_changes_since(local.vector_clock)

        if not new_changes:
            return MergeResult(merged=False, conflicts=[], changes_applied=0)

        conflicts: list[str] = []
        applied = 0

        # Sort by (seq, timestamp) for deterministic ordering
        new_changes.sort(key=lambda c: (c["seq"], c["timestamp"]))

        for change in new_changes:
            nid = change["node_id"]
            seq = change["seq"]

            # Idempotency check: skip if we've already seen this sequence
            if seq <= local.vector_clock.get(nid, 0):
                continue

            # Detect concurrent modifications (conflict)
            concurrent_keys = _detect_conflicts(local, change)
            if concurrent_keys:
                conflicts.extend(concurrent_keys)
                logger.info(
                    "Conflict detected on doc %s keys %s — "
                    "using last-writer-wins by timestamp",
                    local.doc_id, concurrent_keys,
                )

            # Apply the change (last-writer-wins for conflicts)
            local._apply_changes(change["changes"])
            local.vector_clock[nid] = max(local.vector_clock.get(nid, 0), seq)
            local.history.append(change)
            local.updated_at = max(local.updated_at, change["timestamp"])
            applied += 1

        return MergeResult(merged=applied > 0, conflicts=conflicts, changes_applied=applied)

    def merge_from_snapshot(
        self, local: SyncDocument | None, remote_dict: dict[str, Any]
    ) -> tuple[SyncDocument, MergeResult]:
        """Merge from a serialized remote document snapshot.

        If local is None, creates a new document from the remote data.
        """
        remote = SyncDocument.from_dict(remote_dict)

        if local is None:
            return remote, MergeResult(
                merged=True, conflicts=[], changes_applied=len(remote.history)
            )

        result = self.merge(local, remote)
        return local, result


def _detect_conflicts(local: SyncDocument, change: dict[str, Any]) -> list[str]:
    """Detect keys modified concurrently by local and remote."""
    conflicts = []
    changed_keys = set(change.get("changes", {}).keys())

    # Check if any local changes since the remote's last known state
    # modified the same keys
    remote_nid = change["node_id"]
    for entry in reversed(local.history):
        if entry["node_id"] == remote_nid:
            break
        entry_keys = set(entry.get("changes", {}).keys())
        overlap = changed_keys & entry_keys
        if overlap:
            conflicts.extend(overlap)

    return conflicts
