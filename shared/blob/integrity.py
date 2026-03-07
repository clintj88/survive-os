"""Integrity verification for content-addressed blobs.

Verify blob hash matches content, detect corruption.
"""

from .store import _blob_path, hash_content, list_blobs, read_bytes


def verify_blob(base_dir: str, content_hash: str) -> bool:
    """Verify a single blob's integrity. Returns True if hash matches content."""
    blob = _blob_path(base_dir, content_hash)
    if not blob.exists():
        return False
    data = blob.read_bytes()
    return hash_content(data) == content_hash


def find_corrupted(base_dir: str) -> list[str]:
    """Scan all blobs and return hashes of corrupted ones."""
    corrupted = []
    for h in list_blobs(base_dir):
        if not verify_blob(base_dir, h):
            corrupted.append(h)
    return corrupted


def verify_all(base_dir: str) -> dict[str, bool]:
    """Verify all blobs. Returns dict of hash -> is_valid."""
    results = {}
    for h in list_blobs(base_dir):
        results[h] = verify_blob(base_dir, h)
    return results
