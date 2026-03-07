"""Content-addressed blob storage engine.

Files stored by SHA-256 hash with automatic deduplication.
Storage layout: <base_dir>/<first 2 hex>/<next 2 hex>/<full hash>
Metadata sidecar stored alongside as <hash>.meta.json.
"""

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import BinaryIO

from shared.db.timestamps import utcnow

DEFAULT_CHUNK_SIZE = 64 * 1024  # 64KB, friendly for Pi SD cards


def _blob_dir(base_dir: str, content_hash: str) -> Path:
    return Path(base_dir) / content_hash[:2] / content_hash[2:4]


def _blob_path(base_dir: str, content_hash: str) -> Path:
    return _blob_dir(base_dir, content_hash) / content_hash


def _meta_path(base_dir: str, content_hash: str) -> Path:
    return _blob_dir(base_dir, content_hash) / f"{content_hash}.meta.json"


def hash_content(data: bytes) -> str:
    """Compute SHA-256 hash of bytes content."""
    return hashlib.sha256(data).hexdigest()


def hash_stream(stream: BinaryIO, chunk_size: int = DEFAULT_CHUNK_SIZE) -> str:
    """Compute SHA-256 hash of a stream without loading it all into memory."""
    h = hashlib.sha256()
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        h.update(chunk)
    return h.hexdigest()


def store_bytes(
    base_dir: str,
    data: bytes,
    filename: str = "",
    mime_type: str = "application/octet-stream",
) -> str:
    """Store bytes content. Returns the content hash.

    If content already exists (same hash), the blob is not rewritten
    but metadata is updated if filename/mime_type differ.
    """
    content_hash = hash_content(data)
    blob = _blob_path(base_dir, content_hash)

    if not blob.exists():
        blob.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write: temp file then rename
        fd, tmp = tempfile.mkstemp(dir=blob.parent)
        try:
            os.write(fd, data)
            os.close(fd)
            fd = -1
            os.rename(tmp, str(blob))
        except Exception:
            if fd >= 0:
                os.close(fd)
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    _write_metadata(base_dir, content_hash, filename, mime_type, len(data))
    return content_hash


def store_stream(
    base_dir: str,
    stream: BinaryIO,
    filename: str = "",
    mime_type: str = "application/octet-stream",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> str:
    """Store content from a stream. Returns the content hash.

    Streams to a temp file, computes hash, then atomically moves into place.
    """
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)

    h = hashlib.sha256()
    size = 0
    fd, tmp = tempfile.mkstemp(dir=str(base))
    try:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            os.write(fd, chunk)
            h.update(chunk)
            size += len(chunk)
        os.close(fd)

        content_hash = h.hexdigest()
        blob = _blob_path(base_dir, content_hash)

        if blob.exists():
            os.unlink(tmp)
        else:
            blob.parent.mkdir(parents=True, exist_ok=True)
            os.rename(tmp, str(blob))
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise

    _write_metadata(base_dir, content_hash, filename, mime_type, size)
    return content_hash


def read_bytes(base_dir: str, content_hash: str) -> bytes:
    """Read blob content as bytes. Raises FileNotFoundError if missing."""
    blob = _blob_path(base_dir, content_hash)
    return blob.read_bytes()


def read_stream(
    base_dir: str, content_hash: str, chunk_size: int = DEFAULT_CHUNK_SIZE
) -> BinaryIO:
    """Open blob for streaming read. Caller must close the returned file."""
    blob = _blob_path(base_dir, content_hash)
    return open(blob, "rb")


def exists(base_dir: str, content_hash: str) -> bool:
    """Check if a blob exists in the store."""
    return _blob_path(base_dir, content_hash).exists()


def get_metadata(base_dir: str, content_hash: str) -> dict | None:
    """Read blob metadata sidecar. Returns None if not found."""
    meta = _meta_path(base_dir, content_hash)
    if not meta.exists():
        return None
    return json.loads(meta.read_text())


def delete_blob(base_dir: str, content_hash: str) -> bool:
    """Physically remove a blob and its metadata. Returns True if removed."""
    blob = _blob_path(base_dir, content_hash)
    meta = _meta_path(base_dir, content_hash)
    removed = False
    if blob.exists():
        blob.unlink()
        removed = True
    if meta.exists():
        meta.unlink()
    # Clean up empty parent directories
    for parent in [blob.parent, blob.parent.parent]:
        try:
            parent.rmdir()
        except OSError:
            break
    return removed


def list_blobs(base_dir: str) -> list[str]:
    """List all blob hashes in the store."""
    base = Path(base_dir)
    hashes = []
    if not base.exists():
        return hashes
    for d1 in sorted(base.iterdir()):
        if not d1.is_dir() or len(d1.name) != 2:
            continue
        for d2 in sorted(d1.iterdir()):
            if not d2.is_dir() or len(d2.name) != 2:
                continue
            for f in sorted(d2.iterdir()):
                if f.is_file() and not f.name.endswith(".meta.json"):
                    hashes.append(f.name)
    return hashes


def _write_metadata(
    base_dir: str, content_hash: str, filename: str, mime_type: str, size: int
) -> None:
    meta = _meta_path(base_dir, content_hash)
    meta.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "hash": content_hash,
        "filename": filename,
        "mime_type": mime_type,
        "size": size,
        "created_at": utcnow(),
    }
    meta.write_text(json.dumps(data, indent=2))
