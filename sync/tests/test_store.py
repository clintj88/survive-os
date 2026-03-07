"""Tests for DocumentStore."""

import tempfile
from pathlib import Path

import pytest

from sync.engine.document import SyncDocument
from sync.engine.store import DocumentStore


@pytest.fixture
def tmp_store():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        storage_path = str(Path(tmpdir) / "docs")
        store = DocumentStore(db_path=db_path, storage_path=storage_path)
        store.init()
        yield store
        store.close()


def test_save_and_load(tmp_store: DocumentStore):
    doc = SyncDocument(doc_type="test", node_id="node-1", data={"key": "value"})
    tmp_store.save(doc)

    loaded = tmp_store.load(doc.doc_id)
    assert loaded is not None
    assert loaded.doc_id == doc.doc_id
    assert loaded.data["key"] == "value"


def test_load_nonexistent(tmp_store: DocumentStore):
    assert tmp_store.load("nonexistent") is None


def test_delete(tmp_store: DocumentStore):
    doc = SyncDocument(doc_type="test", node_id="node-1")
    tmp_store.save(doc)
    tmp_store.delete(doc.doc_id)
    assert tmp_store.load(doc.doc_id) is None


def test_list_by_type(tmp_store: DocumentStore):
    for i in range(3):
        doc = SyncDocument(doc_type="inventory", node_id="node-1", data={"i": i})
        tmp_store.save(doc)
    doc_other = SyncDocument(doc_type="medical", node_id="node-1")
    tmp_store.save(doc_other)

    results = tmp_store.list_by_type("inventory")
    assert len(results) == 3

    results = tmp_store.list_by_type("medical")
    assert len(results) == 1


def test_list_modified_since(tmp_store: DocumentStore):
    doc1 = SyncDocument(doc_type="test", node_id="node-1")
    doc1.updated_at = 100.0
    tmp_store.save(doc1)

    doc2 = SyncDocument(doc_type="test", node_id="node-1")
    doc2.updated_at = 200.0
    tmp_store.save(doc2)

    results = tmp_store.list_modified_since(150.0)
    assert len(results) == 1
    assert results[0]["doc_id"] == doc2.doc_id


def test_count(tmp_store: DocumentStore):
    assert tmp_store.count() == 0
    doc = SyncDocument(doc_type="test", node_id="node-1")
    tmp_store.save(doc)
    assert tmp_store.count() == 1


def test_list_all(tmp_store: DocumentStore):
    for _ in range(5):
        tmp_store.save(SyncDocument(doc_type="test", node_id="node-1"))
    assert len(tmp_store.list_all()) == 5
