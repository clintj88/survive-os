"""Blob sync adapter for the CRDT sync engine.

Provides primitives for announcing, requesting, and transferring
blobs between peers over constrained links (e.g., ham radio).
"""

from dataclasses import dataclass, field
from typing import BinaryIO

from .store import DEFAULT_CHUNK_SIZE, exists, hash_content, read_bytes, store_bytes

DEFAULT_TRANSFER_CHUNK = 8 * 1024  # 8KB chunks for radio transport


@dataclass
class BlobManifest:
    """Announces which blobs a node has available."""
    node_id: str
    hashes: list[str] = field(default_factory=list)


@dataclass
class BlobRequest:
    """Request a specific blob from a peer."""
    blob_hash: str
    offset: int = 0
    chunk_size: int = DEFAULT_TRANSFER_CHUNK


@dataclass
class BlobChunk:
    """A chunk of blob data for transfer."""
    blob_hash: str
    offset: int
    data: bytes
    total_size: int
    is_last: bool


def build_manifest(base_dir: str, node_id: str) -> BlobManifest:
    """Build a manifest of all blobs available locally."""
    from .store import list_blobs
    return BlobManifest(node_id=node_id, hashes=list_blobs(base_dir))


def find_missing(local_dir: str, remote_manifest: BlobManifest) -> list[str]:
    """Determine which blobs from a remote manifest we don't have locally."""
    return [h for h in remote_manifest.hashes if not exists(local_dir, h)]


def read_chunk(base_dir: str, request: BlobRequest) -> BlobChunk | None:
    """Read a chunk of a blob to send to a peer."""
    if not exists(base_dir, request.blob_hash):
        return None
    data = read_bytes(base_dir, request.blob_hash)
    total = len(data)
    end = min(request.offset + request.chunk_size, total)
    chunk_data = data[request.offset:end]
    return BlobChunk(
        blob_hash=request.blob_hash,
        offset=request.offset,
        data=chunk_data,
        total_size=total,
        is_last=end >= total,
    )


class ChunkedReceiver:
    """Receives blob chunks and assembles them into a complete blob."""

    def __init__(self, blob_hash: str, total_size: int) -> None:
        self.blob_hash = blob_hash
        self.total_size = total_size
        self._buffer = bytearray(total_size)
        self._received = 0

    def receive_chunk(self, chunk: BlobChunk) -> bool:
        """Process a received chunk. Returns True when blob is complete."""
        end = chunk.offset + len(chunk.data)
        self._buffer[chunk.offset:end] = chunk.data
        self._received += len(chunk.data)
        return self._received >= self.total_size

    def finalize(self, base_dir: str) -> bool:
        """Verify and store the assembled blob. Returns True on success."""
        data = bytes(self._buffer)
        actual_hash = hash_content(data)
        if actual_hash != self.blob_hash:
            return False
        store_bytes(base_dir, data)
        return True
