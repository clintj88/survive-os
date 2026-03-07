"""Tests for blob integrity verification."""

from shared.blob.integrity import find_corrupted, verify_all, verify_blob
from shared.blob.store import _blob_path, store_bytes


def test_verify_valid_blob(tmp_path):
    base = str(tmp_path / "blobs")
    h = store_bytes(base, b"valid content")
    assert verify_blob(base, h)


def test_verify_corrupted_blob(tmp_path):
    base = str(tmp_path / "blobs")
    h = store_bytes(base, b"original content")
    # Corrupt the blob
    blob = _blob_path(base, h)
    blob.write_bytes(b"corrupted!")
    assert not verify_blob(base, h)


def test_verify_missing_blob(tmp_path):
    base = str(tmp_path / "blobs")
    assert not verify_blob(base, "nonexistent_hash")


def test_find_corrupted(tmp_path):
    base = str(tmp_path / "blobs")
    h1 = store_bytes(base, b"good")
    h2 = store_bytes(base, b"will be bad")
    _blob_path(base, h2).write_bytes(b"corrupted")
    corrupted = find_corrupted(base)
    assert h2 in corrupted
    assert h1 not in corrupted


def test_verify_all(tmp_path):
    base = str(tmp_path / "blobs")
    h1 = store_bytes(base, b"a")
    h2 = store_bytes(base, b"b")
    results = verify_all(base)
    assert results[h1] is True
    assert results[h2] is True
