"""Tests for blob reference tracking and garbage collection."""

import pytest

from shared.db import connect
from shared.blob.refs import (
    add_ref,
    gc_blobs,
    get_refs_for_record,
    get_unreferenced_hashes,
    init_refs_table,
    ref_count,
    remove_all_refs,
    remove_ref,
)
from shared.blob.store import store_bytes


@pytest.fixture
def conn():
    c = connect(":memory:")
    init_refs_table(c)
    return c


@pytest.fixture
def blob_dir(tmp_path):
    return str(tmp_path / "blobs")


class TestRefCounting:
    def test_add_ref(self, conn):
        add_ref(conn, "photo", "rec-1", "hash-a")
        assert ref_count(conn, "hash-a") == 1

    def test_add_duplicate_ref(self, conn):
        add_ref(conn, "photo", "rec-1", "hash-a")
        add_ref(conn, "photo", "rec-1", "hash-a")
        assert ref_count(conn, "hash-a") == 1

    def test_multiple_refs(self, conn):
        add_ref(conn, "photo", "rec-1", "hash-a")
        add_ref(conn, "document", "rec-2", "hash-a")
        assert ref_count(conn, "hash-a") == 2

    def test_remove_ref(self, conn):
        add_ref(conn, "photo", "rec-1", "hash-a")
        add_ref(conn, "document", "rec-2", "hash-a")
        remove_ref(conn, "photo", "rec-1", "hash-a")
        assert ref_count(conn, "hash-a") == 1

    def test_remove_all_refs(self, conn):
        add_ref(conn, "photo", "rec-1", "hash-a")
        add_ref(conn, "photo", "rec-1", "hash-b")
        remove_all_refs(conn, "photo", "rec-1")
        assert ref_count(conn, "hash-a") == 0
        assert ref_count(conn, "hash-b") == 0

    def test_get_refs_for_record(self, conn):
        add_ref(conn, "photo", "rec-1", "hash-a")
        add_ref(conn, "photo", "rec-1", "hash-b")
        refs = get_refs_for_record(conn, "photo", "rec-1")
        assert set(refs) == {"hash-a", "hash-b"}

    def test_unreferenced_hashes(self, conn):
        add_ref(conn, "photo", "rec-1", "hash-a")
        unreferenced = get_unreferenced_hashes(conn, ["hash-a", "hash-b", "hash-c"])
        assert set(unreferenced) == {"hash-b", "hash-c"}


class TestGarbageCollection:
    def test_gc_removes_unreferenced(self, conn, blob_dir):
        h1 = store_bytes(blob_dir, b"keep me")
        h2 = store_bytes(blob_dir, b"delete me")
        add_ref(conn, "photo", "rec-1", h1)
        removed = gc_blobs(conn, blob_dir)
        assert h2 in removed
        assert h1 not in removed

    def test_gc_empty_store(self, conn, blob_dir):
        assert gc_blobs(conn, blob_dir) == []
