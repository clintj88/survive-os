"""Tests for SyncDocument."""

from sync.engine.document import SyncDocument


def test_create_document():
    doc = SyncDocument(doc_type="inventory", node_id="node-1")
    assert doc.doc_id
    assert doc.doc_type == "inventory"
    assert doc.data == {}


def test_update_advances_clock():
    doc = SyncDocument(doc_type="inventory", node_id="node-1")
    doc.update({"item": "seeds", "qty": 10})

    assert doc.vector_clock["node-1"] == 1
    assert doc.data["item"] == "seeds"
    assert len(doc.history) == 1


def test_multiple_updates():
    doc = SyncDocument(doc_type="inventory", node_id="node-1")
    doc.update({"item": "seeds"})
    doc.update({"qty": 50})

    assert doc.vector_clock["node-1"] == 2
    assert doc.data["item"] == "seeds"
    assert doc.data["qty"] == 50
    assert len(doc.history) == 2


def test_get_changes_since():
    doc = SyncDocument(doc_type="inventory", node_id="node-1")
    doc.update({"a": 1})
    doc.update({"b": 2})
    doc.update({"c": 3})

    # Remote has seen seq 1
    changes = doc.get_changes_since({"node-1": 1})
    assert len(changes) == 2
    assert changes[0]["seq"] == 2
    assert changes[1]["seq"] == 3


def test_get_changes_since_empty_clock():
    doc = SyncDocument(doc_type="inventory", node_id="node-1")
    doc.update({"a": 1})

    changes = doc.get_changes_since({})
    assert len(changes) == 1


def test_serialization_roundtrip():
    doc = SyncDocument(doc_type="test", node_id="node-1")
    doc.update({"key": "value"})

    d = doc.to_dict()
    restored = SyncDocument.from_dict(d)

    assert restored.doc_id == doc.doc_id
    assert restored.data == doc.data
    assert restored.vector_clock == doc.vector_clock
    assert len(restored.history) == len(doc.history)


def test_snapshot_hash_deterministic():
    doc = SyncDocument(doc_type="test", node_id="node-1", data={"a": 1, "b": 2})
    h1 = doc.snapshot_hash()
    h2 = doc.snapshot_hash()
    assert h1 == h2


def test_deep_merge_nested():
    doc = SyncDocument(doc_type="test", node_id="node-1")
    doc.update({"config": {"a": 1, "b": 2}})
    doc.update({"config": {"b": 3, "c": 4}})

    assert doc.data["config"] == {"a": 1, "b": 3, "c": 4}
