"""Tests for blob integrity verification."""

import pytest

from shared.blob.integrity import find_corrupted, verify_all, verify_blob
from shared.blob.store import _blob_path, store_bytes


@pytest.fixture
def blob_dir(tmp_path):
    return str(tmp_path / "blobs")


class TestVerifyBlob:
    def test_valid_blob(self, blob_dir):
        h = store_bytes(blob_dir, b"valid content")
        assert verify_blob(blob_dir, h) is True

    def test_corrupted_blob(self, blob_dir):
        h = store_bytes(blob_dir, b"will corrupt")
        blob_path = _blob_path(blob_dir, h)
        blob_path.write_bytes(b"corrupted!")
        assert verify_blob(blob_dir, h) is False

    def test_missing_blob(self, blob_dir):
        assert verify_blob(blob_dir, "deadbeef" * 8) is False


class TestFindCorrupted:
    def test_no_corruption(self, blob_dir):
        store_bytes(blob_dir, b"a")
        store_bytes(blob_dir, b"b")
        assert find_corrupted(blob_dir) == []

    def test_detects_corruption(self, blob_dir):
        h1 = store_bytes(blob_dir, b"good")
        h2 = store_bytes(blob_dir, b"bad")
        _blob_path(blob_dir, h2).write_bytes(b"tampered")
        corrupted = find_corrupted(blob_dir)
        assert h2 in corrupted
        assert h1 not in corrupted


class TestVerifyAll:
    def test_verify_all(self, blob_dir):
        h1 = store_bytes(blob_dir, b"one")
        h2 = store_bytes(blob_dir, b"two")
        results = verify_all(blob_dir)
        assert results[h1] is True
        assert results[h2] is True
