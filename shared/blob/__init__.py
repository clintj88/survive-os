"""Content-addressed blob storage for SURVIVE OS.

Provides deduplicating file storage with reference counting,
integrity verification, optional encryption, and sync support.
"""

from .encryption import decrypt_blob, encrypt_blob
from .integrity import find_corrupted, verify_all, verify_blob
from .refs import (
    add_ref,
    gc_blobs,
    get_refs_for_record,
    get_unreferenced_hashes,
    init_refs_table,
    ref_count,
    remove_all_refs,
    remove_ref,
)
from .store import (
    delete_blob,
    exists,
    get_metadata,
    hash_content,
    hash_stream,
    list_blobs,
    read_bytes,
    read_stream,
    store_bytes,
    store_stream,
)
from .sync import (
    BlobChunk,
    BlobManifest,
    BlobRequest,
    ChunkedReceiver,
    build_manifest,
    find_missing,
    read_chunk,
)

__all__ = [
    # store
    "store_bytes",
    "store_stream",
    "read_bytes",
    "read_stream",
    "exists",
    "delete_blob",
    "list_blobs",
    "get_metadata",
    "hash_content",
    "hash_stream",
    # refs
    "init_refs_table",
    "add_ref",
    "remove_ref",
    "remove_all_refs",
    "ref_count",
    "get_refs_for_record",
    "get_unreferenced_hashes",
    "gc_blobs",
    # integrity
    "verify_blob",
    "find_corrupted",
    "verify_all",
    # encryption
    "encrypt_blob",
    "decrypt_blob",
    # sync
    "BlobManifest",
    "BlobRequest",
    "BlobChunk",
    "ChunkedReceiver",
    "build_manifest",
    "find_missing",
    "read_chunk",
]
