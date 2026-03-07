# shared/blob — Content-Addressed Blob Storage

Stores large objects (images, documents, map tiles, medical files) by SHA-256 hash with automatic deduplication, reference counting, and sync support.

## Quick Start

```python
from shared.blob import store_bytes, read_bytes, exists, get_metadata

# Store a file
content_hash = store_bytes(
    "/var/lib/survive/blobs",
    file_data,
    filename="xray.dcm",
    mime_type="application/dicom",
)

# Read it back
data = read_bytes("/var/lib/survive/blobs", content_hash)
```

## Storage Layout

```
/var/lib/survive/blobs/
  ab/
    cd/
      abcdef1234...       # blob content
      abcdef1234....meta.json  # metadata sidecar
```

Files are stored by their SHA-256 hash in a two-level directory tree (first 2 hex chars / next 2 hex chars). This provides deduplication — identical content is stored only once regardless of how many records reference it.

All writes are atomic (write-to-temp then rename), safe for SD cards and USB drives.

## API Reference

### store — Storage Engine

| Function | Description |
|---|---|
| `store_bytes(base_dir, data, filename, mime_type)` | Store bytes, return content hash |
| `store_stream(base_dir, stream, filename, mime_type)` | Store from stream, return hash |
| `read_bytes(base_dir, hash)` | Read blob as bytes |
| `read_stream(base_dir, hash)` | Open blob for streaming read |
| `exists(base_dir, hash)` | Check if blob exists |
| `get_metadata(base_dir, hash)` | Read metadata sidecar |
| `delete_blob(base_dir, hash)` | Remove blob and metadata |
| `list_blobs(base_dir)` | List all blob hashes |
| `hash_content(data)` | SHA-256 hash of bytes |
| `hash_stream(stream)` | SHA-256 hash of stream |

### refs — Reference Tracking

Uses a SQLite table (`_blob_refs`) to track which records reference which blobs.

```python
from shared.db import connect
from shared.blob import init_refs_table, add_ref, ref_count, gc_blobs

conn = connect("/var/lib/survive/mymodule/data.db")
init_refs_table(conn)

add_ref(conn, "patient_photo", "patient-123", content_hash)
assert ref_count(conn, content_hash) == 1

# Garbage collect unreferenced blobs
removed = gc_blobs(conn, "/var/lib/survive/blobs")
```

### integrity — Verification

```python
from shared.blob import verify_blob, find_corrupted

assert verify_blob("/var/lib/survive/blobs", content_hash)
corrupted = find_corrupted("/var/lib/survive/blobs")
```

### encryption — Optional Encryption at Rest

```python
from shared.blob import encrypt_blob, decrypt_blob

encrypted = encrypt_blob(data, passphrase="module-key")
original = decrypt_blob(encrypted, passphrase="module-key")
```

Requires `cryptography` package. Uses AES-256-GCM with PBKDF2 key derivation.

### sync — Blob Sync Adapter

Primitives for peer-to-peer blob transfer over constrained links:

```python
from shared.blob import build_manifest, find_missing, read_chunk, BlobRequest, ChunkedReceiver

# Announce what we have
manifest = build_manifest("/var/lib/survive/blobs", "node-a")

# Find what we're missing from a peer
missing = find_missing("/var/lib/survive/blobs", remote_manifest)

# Chunked transfer for radio links
request = BlobRequest(blob_hash=hash, offset=0, chunk_size=8192)
chunk = read_chunk("/var/lib/survive/blobs", request)

# Reassemble on receiving end
receiver = ChunkedReceiver(blob_hash, total_size)
receiver.receive_chunk(chunk)
receiver.finalize("/var/lib/survive/blobs")
```

## Running Tests

```bash
cd shared/blob
python3 -m pytest tests/ -v
```
