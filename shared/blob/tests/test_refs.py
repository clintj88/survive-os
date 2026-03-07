"""Tests for blob reference tracking."""

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
from shared.db import connect


def _setup(tmp_path=None):
    conn = connect(":memory:")
    init_refs_table(conn)
    base = str(tmp_path / "blobs") if tmp_path else None
    return conn, base


def test_add_and_count():
    conn, _ = _setup()
    add_ref(conn, "photo", "rec-1", "hash-abc")
    assert ref_count(conn, "hash-abc") == 1
    add_ref(conn, "photo", "rec-2", "hash-abc")
    assert ref_count(conn, "hash-abc") == 2


def test_add_idempotent():
    conn, _ = _setup()
    add_ref(conn, "photo", "rec-1", "hash-abc")
    add_ref(conn, "photo", "rec-1", "hash-abc")  # duplicate
    assert ref_count(conn, "hash-abc") == 1


def test_remove_ref():
    conn, _ = _setup()
    add_ref(conn, "photo", "rec-1", "hash-abc")
    remove_ref(conn, "photo", "rec-1", "hash-abc")
    assert ref_count(conn, "hash-abc") == 0


def test_remove_all_refs():
    conn, _ = _setup()
    add_ref(conn, "photo", "rec-1", "hash-a")
    add_ref(conn, "photo", "rec-1", "hash-b")
    remove_all_refs(conn, "photo", "rec-1")
    assert ref_count(conn, "hash-a") == 0
    assert ref_count(conn, "hash-b") == 0


def test_get_refs_for_record():
    conn, _ = _setup()
    add_ref(conn, "photo", "rec-1", "hash-a")
    add_ref(conn, "photo", "rec-1", "hash-b")
    refs = get_refs_for_record(conn, "photo", "rec-1")
    assert set(refs) == {"hash-a", "hash-b"}


def test_unreferenced_hashes():
    conn, _ = _setup()
    add_ref(conn, "photo", "rec-1", "hash-a")
    unreferenced = get_unreferenced_hashes(conn, ["hash-a", "hash-b", "hash-c"])
    assert set(unreferenced) == {"hash-b", "hash-c"}


def test_gc_blobs(tmp_path):
    conn, base = _setup(tmp_path)
    h1 = store_bytes(base, b"keep me")
    h2 = store_bytes(base, b"delete me")
    add_ref(conn, "photo", "rec-1", h1)
    removed = gc_blobs(conn, base)
    assert h2 in removed
    assert h1 not in removed
