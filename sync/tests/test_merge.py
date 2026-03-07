"""Tests for MergeEngine — idempotent, ordered merge."""

from sync.engine.document import SyncDocument
from sync.engine.merge import MergeEngine


def make_doc(node_id: str, doc_id: str = "doc-1") -> SyncDocument:
    return SyncDocument(doc_id=doc_id, doc_type="test", node_id=node_id)


def test_merge_new_changes():
    engine = MergeEngine()

    local = make_doc("node-1")
    local.update({"a": 1})

    remote = make_doc("node-2", doc_id="doc-1")
    remote.update({"b": 2})

    result = engine.merge(local, remote)

    assert result.merged is True
    assert result.changes_applied == 1
    assert local.data["b"] == 2
    assert "node-2" in local.vector_clock


def test_merge_idempotent():
    """Merging the same data twice produces identical results."""
    engine = MergeEngine()

    local = make_doc("node-1")
    local.update({"a": 1})

    remote = make_doc("node-2", doc_id="doc-1")
    remote.update({"b": 2})

    result1 = engine.merge(local, remote)
    snapshot_after_first = local.snapshot_hash()

    # Merge again — should be a no-op
    result2 = engine.merge(local, remote)

    assert result1.merged is True
    assert result2.merged is False
    assert result2.changes_applied == 0
    assert local.snapshot_hash() == snapshot_after_first


def test_merge_no_changes():
    engine = MergeEngine()

    local = make_doc("node-1")
    remote = make_doc("node-1", doc_id="doc-1")

    result = engine.merge(local, remote)
    assert result.merged is False


def test_merge_detects_conflicts():
    engine = MergeEngine()

    local = make_doc("node-1")
    local.update({"field": "local_value"})

    remote = make_doc("node-2", doc_id="doc-1")
    remote.update({"field": "remote_value"})

    result = engine.merge(local, remote)

    assert result.merged is True
    assert "field" in result.conflicts
    # Last-writer-wins: remote value applied
    assert local.data["field"] == "remote_value"


def test_merge_different_ids_raises():
    engine = MergeEngine()
    local = make_doc("node-1", doc_id="doc-1")
    remote = make_doc("node-2", doc_id="doc-2")

    try:
        engine.merge(local, remote)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_merge_from_snapshot_new_doc():
    engine = MergeEngine()
    remote_dict = make_doc("node-2").to_dict()
    remote_dict["data"] = {"x": 1}

    doc, result = engine.merge_from_snapshot(None, remote_dict)

    assert doc.doc_id == remote_dict["doc_id"]
    assert result.merged is True


def test_merge_from_snapshot_existing():
    engine = MergeEngine()

    local = make_doc("node-1")
    local.update({"a": 1})

    remote = make_doc("node-2", doc_id=local.doc_id)
    remote.update({"b": 2})

    doc, result = engine.merge_from_snapshot(local, remote.to_dict())

    assert result.merged is True
    assert doc.data["a"] == 1
    assert doc.data["b"] == 2
