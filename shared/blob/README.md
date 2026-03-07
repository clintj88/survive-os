# shared/blob — Content-Addressed Blob Storage

Deduplicating file storage for SURVIVE OS. Files stored by SHA-256 hash with reference counting, integrity checks, optional encryption, and sync support.

## Storage Layout

```
/var/lib/survive/blobs/
  ab/
    cd/
      abcdef1234...          # blob content
      abcdef1234...meta.json # metadata sidecar
```

## Quick Start

```python
from shared.blob import store_bytes, read_bytes, exists, get_metadata

# Store a file
content_hash = store_bytes("/var/lib/survive/blobs", b"hello world", filename="hello.txt", mime_type="text/plain")

# Read it back
data = read_bytes("/var/lib/survive/blobs", content_hash)

# Check existence
exists("/var/lib/survive/blobs", content_hash)  # True

# Get metadata
meta = get_metadata("/var/lib/survive/blobs", content_hash)
# {"hash": "...", "filename": "hello.txt", "mime_type": "text/plain", "size": 11, "created_at": "..."}
```

## Reference Counting & GC

```python
from shared.db import connect
from shared.blob import init_refs_table, add_ref, ref_count, gc_blobs

conn = connect("/var/lib/survive/mymodule/data.db")
init_refs_table(conn)

add_ref(conn, "photo", "record-123", content_hash)
ref_count(conn, content_hash)  # 1

# Remove unreferenced blobs
removed = gc_blobs(conn, "/var/lib/survive/blobs")
```

## Integrity Verification

```python
from shared.blob import verify_blob, find_corrupted

verify_blob("/var/lib/survive/blobs", content_hash)  # True/False
corrupted = find_corrupted("/var/lib/survive/blobs")  # list of bad hashes
```

## Encryption (Medical/Security modules)

```python
from shared.blob import encrypt_blob, decrypt_blob

encrypted = encrypt_blob(data, passphrase="module-secret")
decrypted = decrypt_blob(encrypted, passphrase="module-secret")
```

## Sync Over Constrained Links

```python
from shared.blob import build_manifest, find_missing, read_chunk, BlobRequest, ChunkedReceiver

# Sender announces blobs
manifest = build_manifest("/var/lib/survive/blobs", node_id="node-a")

# Receiver finds missing blobs
missing = find_missing("/var/lib/survive/blobs", manifest)

# Chunked transfer (8KB default for radio)
for h in missing:
    req = BlobRequest(blob_hash=h)
    chunk = read_chunk("/var/lib/survive/blobs", req)
    # Send chunk over radio...
```

## Running Tests

```bash
cd shared/blob
python3 -m pytest tests/ -v
```
